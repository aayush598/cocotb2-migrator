#!/usr/bin/env python3
"""
cocotb_migrate.py – *minimal* helper script for migrating Cocotb v1.x test‑benches
to Cocotb v2.x.

It demonstrates a basic end‑to‑end flow using **LibCST** so that you can build
a more sophisticated tool on top:

1.  Recursively scan a directory for ``.py`` files (ignoring virtual‑envs).
2.  Detect the most common v1.x patterns that broke in v2.x.
3.  Optionally **rewrite** the source and save a migrated copy.

Supported migrations (v1 ⇒ v2):
--------------------------------
*   ``@cocotb.coroutine`` decorator → converts the function to ``async def`` and
    removes the decorator.
*   ``yield FooEdge(clk)`` or ``yield Timer(...)`` → ``await FooEdge(clk)``.
    (Works for any single ``yield <call>`` expression.)
*   ``raise ReturnValue(x)`` → ``return x``.
*   ``fork(coro)`` → ``cocotb.start_soon(coro)``.

Usage::

    # show a dry‑run report of what *would* change
    python cocotb_migrate.py --check ../my_tb/

    # rewrite files, producing side‑by‑side *.migrated.py copies
    python cocotb_migrate.py --apply ../my_tb/

    # overwrite files in‑place (no backup!)
    python cocotb_migrate.py --apply --inplace ../my_tb/

The script prints a coloured summary (files changed / unchanged).

> **NOTE**  This is *not* production‑ready – it is intentionally lightweight so
> you have a clear starting point to extend with richer pattern matching,
> config files, unit tests, CI integration, etc.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List

import libcst as cst
import libcst.matchers as m
from termcolor import colored

# -----------------------------------------------------------------------------
# CST Transformer
# -----------------------------------------------------------------------------


class CocotbTransformer(cst.CSTTransformer):
    """Transform a single CST in‑place.

    The transformer is deliberately simple; it only handles *trivial* patterns
    that account for the majority of existing v1.x test‑benches.  LibCST keeps
    formatting and comments intact, so the result is usually ready to run.
    """

    def leave_FunctionDef(  # type: ignore[override]
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Convert "@cocotb.coroutine" → async def."""

        # Look for the decorator and strip it if present.
        decorators = [d for d in updated_node.decorators]
        new_decorators = []
        removed = False
        for dec in decorators:
            if m.matches(
                dec,
                m.Decorator(
                    decorator=m.Attribute(
                        value=m.Name("cocotb"), attr=m.Name("coroutine")
                    )
                ),
            ):
                removed = True
                continue  # drop decorator
            new_decorators.append(dec)

        if removed:
            # Ensure the function is async
            if updated_node.asynchronous is None:
                updated_node = updated_node.with_changes(asynchronous=cst.Asynchronous())
            updated_node = updated_node.with_changes(decorators=new_decorators)
        return updated_node

    # ---------------------------------------------------------------------
    # Replace "yield Something(foo)" → "await Something(foo)"
    # ---------------------------------------------------------------------

    def leave_Yield(  # type: ignore[override]
        self, original_node: cst.Yield, updated_node: cst.Yield
    ) -> cst.Await | cst.Yield:
        # Only transform the easy case: ``yield Call(...)``
        if m.matches(updated_node.value, m.Call()):
            return cst.Await(expression=updated_node.value)
        return updated_node

    # ---------------------------------------------------------------------
    # Replace "raise ReturnValue(x)" → "return x"
    # ---------------------------------------------------------------------

    def leave_Raise(  # type: ignore[override]
        self, original_node: cst.Raise, updated_node: cst.Raise
    ) -> cst.Raise | cst.SimpleStatementLine:
        exc = updated_node.exc
        if m.matches(exc, m.Call(func=m.Name("ReturnValue"))):
            call: cst.Call = exc  # type: ignore[assignment]
            arg = call.args[0].value if call.args else cst.Name("None")
            return cst.SimpleStatementLine(body=[cst.Return(value=arg)])
        return updated_node

    # ---------------------------------------------------------------------
    # Replace "fork(coro)" → "cocotb.start_soon(coro)"
    # ---------------------------------------------------------------------

    def leave_Call(  # type: ignore[override]
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        if m.matches(updated_node.func, m.Name("fork")):
            return updated_node.with_changes(
                func=cst.Attribute(value=cst.Name("cocotb"), attr=cst.Name("start_soon"))
            )
        return updated_node


# -----------------------------------------------------------------------------
# Simple reporting helper
# -----------------------------------------------------------------------------


class ChangeCounter(cst.CSTVisitor):
    """Counts nodes that indicate v1‑only patterns so we can warn the user."""

    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)

    def __init__(self) -> None:
        self.offenses: List[str] = []

    # detect @cocotb.coroutine
    def visit_Decorator(self, node: cst.Decorator) -> None:  # noqa: N802
        if m.matches(
            node,
            m.Decorator(
                decorator=m.Attribute(value=m.Name("cocotb"), attr=m.Name("coroutine"))
            ),
        ):
            self.offenses.append("@cocotb.coroutine decorator")

    # detect yield XEdge(...)
    def visit_Yield(self, node: cst.Yield) -> None:  # noqa: N802
        if m.matches(node.value, m.Call()):
            self.offenses.append("yield <CocotbTrigger>")

    # detect ReturnValue
    def visit_Raise(self, node: cst.Raise) -> None:  # noqa: N802
        if m.matches(node.exc, m.Call(func=m.Name("ReturnValue"))):
            self.offenses.append("raise ReturnValue()")

    # detect fork(...)
    def visit_Call(self, node: cst.Call) -> None:  # noqa: N802
        if m.matches(node.func, m.Name("fork")):
            self.offenses.append("fork() call")


# -----------------------------------------------------------------------------
# CLI glue
# -----------------------------------------------------------------------------


def _colour(b: bool, txt: str) -> str:
    return colored(txt, "green" if b else "yellow")


def migrate_file(path: Path, apply: bool, inplace: bool) -> bool:
    """Return True if the file *would* change."""
    source = path.read_text(encoding="utf‑8")
    try:
        original_tree = cst.parse_module(source)
    except Exception as e:  # pragma: no cover
        print(colored(f"[error] Failed to parse {path}: {e}", "red"))
        return False

    # Count offenses for --check
    wrapper = cst.metadata.MetadataWrapper(original_tree)
    counter = ChangeCounter()
    wrapper.visit(counter)
    needs_change = bool(counter.offenses)

    if not needs_change and not apply:
        return False

    transformer = CocotbTransformer()
    new_tree = original_tree.visit(transformer)

    changed = new_tree.code != source
    if apply and changed:
        out_path = path if inplace else path.with_suffix(".migrated.py")
        out_path.write_text(new_tree.code, encoding="utf‑8")
    return changed


def walk_py_files(root: Path) -> List[Path]:
    return [
        p
        for p in root.rglob("*.py")
        if "site‑packages" not in p.parts and ".venv" not in p.parts
    ]


def main(argv: List[str] | None = None) -> None:  # noqa: D401
    """CLI entry‑point."""
    parser = argparse.ArgumentParser(description="Minimal Cocotb v1→v2 migrator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="show what would change")
    group.add_argument("--apply", action="store_true", help="rewrite source files")
    parser.add_argument("path", type=Path, help="file or directory to process")
    parser.add_argument(
        "--inplace", action="store_true", help="overwrite original files when applying"
    )
    args = parser.parse_args(argv)

    targets = [args.path] if args.path.is_file() else walk_py_files(args.path)

    changed = 0
    unchanged = 0
    for p in targets:
        if migrate_file(p, apply=args.apply, inplace=args.inplace):
            changed += 1
            print(_colour(True, f"[changed] {p}"))
        else:
            unchanged += 1
            if args.check:
                print(_colour(False, f"[ok]      {p}"))

    # Summary
    print("\nSummary:")
    print(colored(f"  {changed} file(s) changed", "green" if changed else "yellow"))
    print(colored(f"  {unchanged} file(s) unchanged", "cyan"))

    if changed and args.check:
        print(
            colored(
                "Run again with --apply (and optionally --inplace) to rewrite files.",
                "magenta",
            )
        )


if __name__ == "__main__":
    main()
