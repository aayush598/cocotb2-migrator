import libcst as cst

from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class CoroutineToAsyncTransformer(BaseCocotbTransformer):
    name = "CoroutineToAsyncTransformer"

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """
        Convert @cocotb.coroutine / @cocotb.decorators.coroutine decorated
        functions to async def, and remove the decorator.
        """

        new_decorators = []
        is_coroutine = False

        for decorator in original_node.decorators:
            if self._is_coroutine_decorator(decorator.decorator):
                is_coroutine = True
                self.mark_modified()
                continue
            new_decorators.append(decorator)

        if is_coroutine:
            return updated_node.with_changes(
                asynchronous=cst.Asynchronous(whitespace_after=cst.SimpleWhitespace(" ")),
                decorators=new_decorators,
            )
        return updated_node

    @staticmethod
    def _is_coroutine_decorator(dec: cst.BaseExpression) -> bool:
        """
        Matches @cocotb.coroutine, @cocotb.decorators.coroutine and their
        call forms (e.g. @cocotb.coroutine()).
        """
        if isinstance(dec, cst.Call):
            return CoroutineToAsyncTransformer._is_coroutine_decorator(dec.func)

        if isinstance(dec, cst.Attribute):
            # @cocotb.coroutine
            if (
                isinstance(dec.value, cst.Name)
                and dec.value.value == "cocotb"
                and dec.attr.value == "coroutine"
            ):
                return True
            # @cocotb.decorators.coroutine
            if (
                isinstance(dec.value, cst.Attribute)
                and isinstance(dec.value.value, cst.Name)
                and dec.value.value.value == "cocotb"
                and dec.value.attr.value == "decorators"
                and dec.attr.value == "coroutine"
            ):
                return True

        return False
