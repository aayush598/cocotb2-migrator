import libcst as cst
from libcst import Attribute, Name
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class HandleTransformer(BaseCocotbTransformer):
    name = "HandleTransformer"

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        """
        Update deprecated handle attributes, such as:
        - handle.value.get_value() -> handle.value
        - handle.value.integer    -> int(handle.value)
        - handle.value.binstr     -> format(handle.value, 'b')
        - handle.value.raw_value  -> handle.value
        """
        if isinstance(original_node.attr, cst.Name) and isinstance(original_node.value, cst.Attribute):
            base = original_node.value
            attr = original_node.attr.value

            if isinstance(base.attr, cst.Name) and base.attr.value == "value":
                if attr == "get_value":
                    # handle.value.get_value() -> handle.value
                    self.mark_modified()
                    return base

                elif attr == "integer":
                    # handle.value.integer -> int(handle.value)
                    self.mark_modified()
                    return cst.Call(
                        func=cst.Name("int"),
                        args=[cst.Arg(value=base)]
                    )

                elif attr == "binstr":
                    # handle.value.binstr -> format(handle.value, 'b')
                    self.mark_modified()
                    return cst.Call(
                        func=cst.Name("format"),
                        args=[
                            cst.Arg(value=base),
                            cst.Arg(value=cst.SimpleString("'b'"))
                        ]
                    )

                elif attr == "raw_value":
                    # handle.value.raw_value -> handle.value
                    self.mark_modified()
                    return base

        return updated_node

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        """
        Remove .get_value() calls: handle.value.get_value() -> handle.value
        """
        if isinstance(original_node.func, cst.Attribute):
            func_attr = original_node.func
            if (
                isinstance(func_attr.value, cst.Attribute) and
                func_attr.attr.value == "get_value" and
                isinstance(func_attr.value.attr, cst.Name) and
                func_attr.value.attr.value == "value"
            ):
                self.mark_modified()
                return func_attr.value

        return updated_node
