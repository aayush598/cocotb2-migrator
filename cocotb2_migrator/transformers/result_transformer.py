import libcst as cst
from typing import Dict, List, Optional

from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class ResultTransformer(BaseCocotbTransformer):
    """
    Rewrites usages of symbols that were removed with the ``cocotb.result`` module.

    raise cocotb.result.TestSuccess(msg) / raise TestSuccess(msg)  ->  cocotb.pass_test(msg)
    raise cocotb.result.TestFailure(msg) / raise TestFailure(msg)  ->  assert False, msg
    raise cocotb.result.TestError(msg)   / raise TestError(msg)    ->  assert False, msg
    raise cocotb.result.ReturnValue(val) / raise ReturnValue(val)  ->  return val
    raise_error(msg)                      ->  assert False, msg
    create_error(msg)                     ->  AssertionError(msg)
    cocotb.result.SimTimeoutError         ->  cocotb.triggers.SimTimeoutError
    cocotb.result.TestComplete            ->  removed (warning emitted)

    Bare symbols (e.g. ``raise TestFailure("...")``) are only rewritten when
    the name was imported from ``cocotb.result`` (including aliased imports),
    avoiding false positives on user-defined names.
    """

    name = "ResultTransformer"

    #: cocotb.result symbol -> replacement kind.
    _REPLACEMENTS = {
        "TestSuccess": "pass_test",
        "TestFailure": "assert_false",
        "TestError": "assert_false",
        "ReturnValue": "return",
        "TestComplete": "warn",
    }

    _ERROR_FUNCS = {"raise_error", "create_error"}

    def __init__(self):
        super().__init__()
        #: local name (incl. aliases) -> original cocotb.result symbol
        self._result_imports: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Import tracking (bare names are only migrated when imported)
    # ------------------------------------------------------------------
    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        if original_node.module and self._module_full_name(original_node.module) == "cocotb.result":
            for alias in original_node.names:
                if isinstance(alias, cst.ImportAlias) and isinstance(alias.name, cst.Name):
                    original_symbol = alias.name.value
                    local_name = (
                        alias.asname.name.value if alias.asname else original_symbol
                    )
                    self._result_imports[local_name] = original_symbol
        return updated_node

    # ------------------------------------------------------------------
    # raise ... -> pass_test / assert / return
    # ------------------------------------------------------------------
    def leave_Raise(
        self, original_node: cst.Raise, updated_node: cst.Raise
    ) -> cst.BaseStatement:
        exc = original_node.exc
        if exc is None or not isinstance(exc, cst.Call):
            return updated_node

        symbol = self._resolve_symbol(exc.func)
        kind = self._REPLACEMENTS.get(symbol or "")
        if kind is None:
            return updated_node

        args = list(exc.args)
        msg = args[0].value if args else None

        if kind == "pass_test":
            self.mark_modified()
            return cst.Expr(
                value=cst.Call(
                    func=cst.Attribute(value=cst.Name("cocotb"), attr=cst.Name("pass_test")),
                    args=args,
                )
            )

        if kind == "assert_false":
            self.mark_modified()
            return cst.Assert(test=cst.Name("False"), msg=msg)

        if kind == "return":
            self.mark_modified()
            return cst.Return(value=msg)

        if kind == "warn":
            self.add_warning(
                f"`{symbol}` was removed in cocotb 2.0 with no direct replacement; update manually"
            )
            return updated_node

        return updated_node

    # ------------------------------------------------------------------
    # raise_error(msg) statement -> assert False, msg
    # ------------------------------------------------------------------
    def leave_Expr(
        self, original_node: cst.Expr, updated_node: cst.Expr
    ) -> cst.BaseStatement:
        value = original_node.value
        if not isinstance(value, cst.Call):
            return updated_node
        if self._resolve_error_func(value.func) != "raise_error":
            return updated_node

        args = list(value.args)
        msg = args[0].value if args else None
        self.mark_modified()
        return cst.Assert(test=cst.Name("False"), msg=msg)

    # ------------------------------------------------------------------
    # create_error(msg) -> AssertionError(msg) (any expression context)
    # ------------------------------------------------------------------
    def leave_Call(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.BaseExpression:
        if self._resolve_error_func(original_node.func) == "create_error":
            self.mark_modified()
            return updated_node.with_changes(func=cst.Name("AssertionError"))
        return updated_node

    # ------------------------------------------------------------------
    # cocotb.result.SimTimeoutError -> cocotb.triggers.SimTimeoutError
    # ------------------------------------------------------------------
    def leave_Attribute(
        self, original_node: cst.Attribute, updated_node: cst.Attribute
    ) -> cst.BaseExpression:
        symbol = self._resolve_cocotb_result_attr(original_node)
        if symbol == "SimTimeoutError":
            self.mark_modified()
            return cst.Attribute(
                value=cst.Attribute(value=cst.Name("cocotb"), attr=cst.Name("triggers")),
                attr=cst.Name("SimTimeoutError"),
            )
        if symbol == "TestComplete":
            self.add_warning(
                "`cocotb.result.TestComplete` was removed in cocotb 2.0 with no direct replacement; update manually"
            )
        return updated_node

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_symbol(self, func: cst.BaseExpression) -> Optional[str]:
        """Resolve a raise target to a known cocotb.result symbol, or None."""
        if isinstance(func, cst.Name):
            symbol = self._result_imports.get(func.value)
            if symbol is not None and self._REPLACEMENTS.get(symbol) is not None:
                return symbol
            return None
        return self._resolve_cocotb_result_attr(func)

    def _resolve_error_func(self, func: cst.BaseExpression) -> Optional[str]:
        """Resolve a call target to 'raise_error'/'create_error', or None."""
        if isinstance(func, cst.Name):
            symbol = self._result_imports.get(func.value)
            if symbol in self._ERROR_FUNCS:
                return symbol
            return None
        symbol = self._resolve_cocotb_result_attr(func)
        if symbol in self._ERROR_FUNCS:
            return symbol
        return None

    @staticmethod
    def _resolve_cocotb_result_attr(node: cst.BaseExpression) -> Optional[str]:
        """Return the symbol for ``cocotb.result.<symbol>``, or None."""
        if not isinstance(node, cst.Attribute) or not isinstance(node.attr, cst.Name):
            return None
        inner = node.value
        if not (
            isinstance(inner, cst.Attribute)
            and isinstance(inner.attr, cst.Name)
            and inner.attr.value == "result"
        ):
            return None
        if not (isinstance(inner.value, cst.Name) and inner.value.value == "cocotb"):
            return None
        return node.attr.value

    @staticmethod
    def _module_full_name(module: cst.BaseExpression) -> str:
        """Extract the full dotted name from a module expression."""
        parts: List[str] = []
        while isinstance(module, cst.Attribute):
            parts.append(module.attr.value)
            module = module.value
        if isinstance(module, cst.Name):
            parts.append(module.value)
        return ".".join(reversed(parts))

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        return self.prepend_warnings(updated_node)
