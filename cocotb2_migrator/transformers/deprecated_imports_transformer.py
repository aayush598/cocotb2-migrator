import libcst as cst
from typing import Dict, List, Optional, Tuple

from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class DeprecatedImportsTransformer(BaseCocotbTransformer):
    """
    Rewrites imports that reference cocotb modules removed in 2.x.

    cocotb.decorators (module removed):
        coroutine / test  ->  cocotb
        external          ->  cocotb.task.bridge (aliased to preserve references)
        function          ->  cocotb.task.resume (aliased to preserve references)
        public            ->  removed (warning emitted)

    cocotb.result (module removed):
        SimTimeoutError   ->  cocotb.triggers.SimTimeoutError
        TestSuccess / TestFailure / TestError / ReturnValue / raise_error / create_error
                          ->  imports removed (usages are rewritten by ResultTransformer)
        TestComplete      ->  removed (warning emitted)

    cocotb.regression (module removed):
        imports removed entirely

    Import statements are rewritten at module level so that names mapping to
    different target modules are emitted as clean, separate statements.
    """

    name = "DeprecatedImportsTransformer"

    #: cocotb.decorators symbol -> (replacement module, replacement name);
    #: None means the symbol was removed with no direct replacement.
    _DECORATORS: Dict[str, Optional[Tuple[str, str]]] = {
        "coroutine": ("cocotb", "coroutine"),
        "test": ("cocotb", "test"),
        "external": ("cocotb.task", "bridge"),
        "function": ("cocotb.task", "resume"),
        "public": None,
    }

    #: cocotb.result symbol -> (replacement module, replacement name);
    #: None means the symbol was removed (usages migrated elsewhere).
    _RESULT: Dict[str, Optional[Tuple[str, str]]] = {
        "SimTimeoutError": ("cocotb.triggers", "SimTimeoutError"),
        "TestSuccess": None,
        "TestFailure": None,
        "TestError": None,
        "TestComplete": None,
        "ReturnValue": None,
        "raise_error": None,
        "create_error": None,
    }

    #: Symbols that carry no replacement and deserve an explicit warning.
    _WARNED_SYMBOLS = {"public", "TestComplete"}

    #: Modules whose imports are fully removed.
    _REMOVED_MODULES = {"cocotb.regression"}

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Rewrite deprecated imports and prepend any warnings as comments."""
        new_body: List[cst.BaseStatement] = []
        for stmt in updated_node.body:
            replacements = self._maybe_transform_import_line(stmt)
            if replacements is None:
                new_body.append(stmt)
            else:
                new_body.extend(replacements)
                self.mark_modified()
        return self.prepend_warnings(updated_node.with_changes(body=new_body))

    def _maybe_transform_import_line(
        self, stmt: cst.BaseStatement
    ) -> Optional[List[cst.BaseStatement]]:
        """
        Returns a list of replacement statements for a deprecated import line,
        [] if the line should be removed, or None if the line is untouched.
        """
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        small = stmt.body[0]

        if isinstance(small, cst.ImportFrom):
            new_imports = self._transform_import_from(small)
            if new_imports is None:
                return None
            if not new_imports:
                return []
            return self._split_imports(stmt, new_imports)

        if isinstance(small, cst.Import):
            new_imports = self._transform_import(small)
            if new_imports is None:
                return None
            if not new_imports:
                return []
            return self._split_imports(stmt, new_imports)

        return None

    @staticmethod
    def _split_imports(
        stmt: cst.SimpleStatementLine, imports: List[cst.BaseSmallStatement]
    ) -> List[cst.BaseStatement]:
        """
        Emit each replacement import as its own statement line so imports that
        target different modules are not joined with semicolons.
        """
        lines: List[cst.BaseStatement] = []
        for i, imp in enumerate(imports):
            line: cst.SimpleStatementLine = cst.SimpleStatementLine(body=(imp,))
            if i == 0:
                line = line.with_changes(leading_lines=stmt.leading_lines)
            lines.append(line)
        return lines

    # ------------------------------------------------------------------
    # ImportFrom handling
    # ------------------------------------------------------------------
    def _transform_import_from(self, node: cst.ImportFrom) -> Optional[List[cst.ImportFrom]]:
        """
        Returns replacement ImportFrom statements, [] if removed, or None if
        the statement is not a deprecated import that needs changing.
        """
        if not node.module:
            return None
        module_name = self.get_full_name(node.module)

        if module_name in self._REMOVED_MODULES:
            self.mark_modified()
            return []

        mapping = self._mapping_for(module_name)
        if mapping is None:
            return None

        if isinstance(node.names, cst.ImportStar):
            self.mark_modified()
            self.add_warning(
                f"`from {module_name} import *` cannot be migrated automatically; update manually"
            )
            return []

        groups: Dict[str, List[cst.ImportAlias]] = {}
        changed = False

        for alias in node.names:
            if not isinstance(alias, cst.ImportAlias) or not isinstance(alias.name, cst.Name):
                # Unusual alias form (e.g. submodule import) - preserve as-is.
                groups.setdefault(module_name, []).append(alias)
                continue

            symbol = alias.name.value
            target = mapping.get(symbol)

            if target is None and symbol in mapping:
                # Known symbol with no replacement (removed in cocotb 2.x).
                changed = True
                if symbol in self._WARNED_SYMBOLS:
                    self.add_warning(
                        f"`{symbol}` was removed in cocotb 2.0 with no direct replacement; update manually"
                    )
                continue

            if target is None:
                # Unknown symbol in a deprecated module - preserve + warn.
                self.add_warning(
                    f"`{module_name}.{symbol}` has no known migration; verify manually"
                )
                groups.setdefault(module_name, []).append(alias)
                continue

            replacement_module, replacement_name = target
            changed = True
            if alias.asname is not None:
                new_alias = alias.with_changes(name=cst.Name(replacement_name))
            elif replacement_name != symbol:
                new_alias = cst.ImportAlias(
                    name=cst.Name(replacement_name),
                    asname=cst.AsName(name=cst.Name(symbol)),
                )
            else:
                new_alias = cst.ImportAlias(name=cst.Name(replacement_name))
            groups.setdefault(replacement_module, []).append(new_alias)

        if not changed:
            return None

        return [
            cst.ImportFrom(module=cst.parse_expression(module), names=names)
            for module, names in groups.items()
        ]

    # ------------------------------------------------------------------
    # Plain `import` handling
    # ------------------------------------------------------------------
    def _transform_import(self, node: cst.Import) -> Optional[List[cst.Import]]:
        """Remove deprecated plain imports (e.g. `import cocotb.result`)."""
        new_names: List[cst.ImportAlias] = []
        changed = False
        for alias in node.names:
            if isinstance(alias, cst.ImportAlias) and isinstance(
                alias.name, (cst.Name, cst.Attribute)
            ):
                full = self.get_full_name(alias.name)
                if full in self._REMOVED_MODULES or full in (
                    "cocotb.decorators",
                    "cocotb.result",
                ):
                    changed = True
                    self.add_warning(
                        f"`import {full}` was removed in cocotb 2.0; update references manually"
                    )
                    continue
            new_names.append(alias)
        if not changed:
            return None
        if not new_names:
            return []
        return [node.with_changes(names=new_names)]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _mapping_for(self, module_name: str) -> Optional[Dict[str, Optional[Tuple[str, str]]]]:
        if module_name == "cocotb.decorators":
            return self._DECORATORS
        if module_name == "cocotb.result":
            return self._RESULT
        return None

    @staticmethod
    def get_full_name(module: cst.BaseExpression) -> str:
        """Extract the full dotted name from a module expression."""
        parts: List[str] = []
        while isinstance(module, cst.Attribute):
            parts.append(module.attr.value)
            module = module.value
        if isinstance(module, cst.Name):
            parts.append(module.value)
        return ".".join(reversed(parts))
