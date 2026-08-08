import libcst as cst
from typing import Dict, Optional, Tuple

from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class DecoratorsTransformer(BaseCocotbTransformer):
    """
    Rewrites references to symbols from the removed ``cocotb.decorators`` module.

        cocotb.decorators.coroutine  ->  cocotb.coroutine
        cocotb.decorators.test       ->  cocotb.test
        cocotb.decorators.external   ->  cocotb.task.bridge
        cocotb.decorators.function   ->  cocotb.task.resume
        cocotb.decorators.public     ->  removed (warning emitted)

    Import statements are handled by DeprecatedImportsTransformer; this
    transformer fixes remaining qualified references to the old module path.
    """

    name = "DecoratorsTransformer"

    #: cocotb.decorators symbol -> (replacement module, replacement name)
    _MAPPING: Dict[str, Tuple[str, str]] = {
        "coroutine": ("cocotb", "coroutine"),
        "test": ("cocotb", "test"),
        "external": ("cocotb.task", "bridge"),
        "function": ("cocotb.task", "resume"),
    }

    def leave_Attribute(
        self, original_node: cst.Attribute, updated_node: cst.Attribute
    ) -> cst.BaseExpression:
        symbol = self._resolve_cocotb_decorators_attr(original_node)
        if symbol is None:
            return updated_node

        if symbol == "public":
            self.add_warning(
                "`cocotb.decorators.public` was removed in cocotb 2.0 with no direct replacement; remove it manually"
            )
            return updated_node

        target = self._MAPPING.get(symbol)
        if target is None:
            self.add_warning(
                f"`cocotb.decorators.{symbol}` has no known migration; verify manually"
            )
            return updated_node

        module, name = target
        self.mark_modified()
        return cst.Attribute(value=cst.parse_expression(module), attr=cst.Name(name))

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        return self.prepend_warnings(updated_node)

    @staticmethod
    def _resolve_cocotb_decorators_attr(node: cst.BaseExpression) -> Optional[str]:
        """Return the symbol for ``cocotb.decorators.<symbol>``, or None."""
        if not isinstance(node, cst.Attribute) or not isinstance(node.attr, cst.Name):
            return None
        inner = node.value
        if not (
            isinstance(inner, cst.Attribute)
            and isinstance(inner.attr, cst.Name)
            and inner.attr.value == "decorators"
        ):
            return None
        if not (isinstance(inner.value, cst.Name) and inner.value.value == "cocotb"):
            return None
        return node.attr.value
