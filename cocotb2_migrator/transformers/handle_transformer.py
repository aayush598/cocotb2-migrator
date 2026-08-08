import libcst as cst
from libcst import Attribute, Name
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class HandleTransformer(BaseCocotbTransformer):
    name = "HandleTransformer"

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        """
        Update deprecated handle attributes, such as:
        - handle.value.integer -> int(handle.value)
        - handle.value.binstr  -> str(handle.value)
        """
        if isinstance(original_node.attr, cst.Name) and isinstance(original_node.value, cst.Attribute):
            base = original_node.value
            attr = original_node.attr.value

            if isinstance(base.attr, cst.Name) and base.attr.value == "value":
                if attr == "integer":
                    # handle.value.integer -> int(handle.value)
                    self.mark_modified()
                    return cst.Call(
                        func=cst.Name("int"),
                        args=[cst.Arg(value=base)]
                    )

                elif attr == "binstr":
                    # handle.value.binstr -> str(handle.value)
                    self.mark_modified()
                    return cst.Call(
                        func=cst.Name("str"),
                        args=[cst.Arg(value=base)]
                    )

        return updated_node
