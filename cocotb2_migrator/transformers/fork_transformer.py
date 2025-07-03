import libcst as cst
from libcst import Call, Attribute, Name
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class ForkTransformer(BaseCocotbTransformer):
    name = "ForkTransformer"

    def leave_Call(self, original_node: Call, updated_node: Call) -> cst.BaseExpression:
        """
        Transforms cocotb.fork(coro()) to cocotb.start_soon(coro()).
        """
        # Match cocotb.fork(...)
        if isinstance(original_node.func, Attribute):
            func = original_node.func
            if (
                isinstance(func.value, Name)
                and func.value.value == "cocotb"
                and func.attr.value == "fork"
            ):
                self.mark_modified()

                # Replace with cocotb.start_soon(...)
                new_func = func.with_changes(attr=Name("start_soon"))
                return updated_node.with_changes(func=new_func)

        return updated_node
