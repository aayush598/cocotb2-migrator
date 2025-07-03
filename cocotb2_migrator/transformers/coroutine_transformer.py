import libcst as cst
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class CoroutineToAsyncTransformer(BaseCocotbTransformer):
    name = "CoroutineToAsyncTransformer"

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """
        Convert @cocotb.coroutine decorated functions to async def,
        and remove the decorator.
        """

        new_decorators = []
        is_coroutine = False

        for decorator in original_node.decorators:
            dec = decorator.decorator

            # Match: @cocotb.coroutine or @cocotb.coroutine()
            if isinstance(dec, cst.Attribute):
                if (
                    isinstance(dec.value, cst.Name)
                    and dec.value.value == "cocotb"
                    and dec.attr.value == "coroutine"
                ):
                    is_coroutine = True
                    self.mark_modified()
                    continue

            elif isinstance(dec, cst.Call):
                # Handle: @cocotb.coroutine()
                func = dec.func
                if (
                    isinstance(func, cst.Attribute)
                    and isinstance(func.value, cst.Name)
                    and func.value.value == "cocotb"
                    and func.attr.value == "coroutine"
                ):
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
