import libcst as cst
from libcst import Attribute, Name, Arg
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class BinaryValueTransformer(BaseCocotbTransformer):
    name = "BinaryValueTransformer"

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        """
        Handle attribute changes like cocotb.binary.BinaryValue -> cocotb.BinaryValue
        """
        # Match cocotb.binary.BinaryValue
        if (
            isinstance(original_node.value, cst.Attribute) and
            isinstance(original_node.value.value, cst.Name) and
            original_node.value.value.value == "cocotb" and
            original_node.value.attr.value == "binary" and
            original_node.attr.value == "BinaryValue"
        ):
            self.mark_modified()
            return cst.Attribute(
                value=cst.Name("cocotb"),
                attr=cst.Name("BinaryValue")
            )
        
        return updated_node

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        """
        Handle instantiation of BinaryValue to make sure keyword arguments are preserved and valid.
        Optionally, we can clean up deprecated arguments (like `bigEndian`) or ensure clarity.
        """
        # Match cocotb.binary.BinaryValue(...) or cocotb.BinaryValue(...)
        if isinstance(original_node.func, (cst.Name, cst.Attribute)):
            func_name = self.get_full_func_name(original_node.func)
            if func_name in {"cocotb.binary.BinaryValue", "cocotb.BinaryValue"}:
                self.mark_modified()

                # Optional: rename deprecated kwargs like bigEndian -> big_endian
                new_args = []
                for arg in updated_node.args:
                    if arg.keyword and arg.keyword.value == "bigEndian":
                        new_args.append(arg.with_changes(keyword=cst.Name("big_endian")))
                    else:
                        new_args.append(arg)

                return updated_node.with_changes(args=new_args)

        return updated_node

    def get_full_func_name(self, func_node) -> str:
        """
        Helper to reconstruct the full dotted name from an Attribute/Name chain.
        """
        if isinstance(func_node, cst.Name):
            return func_node.value
        elif isinstance(func_node, cst.Attribute):
            parts = []
            while isinstance(func_node, cst.Attribute):
                parts.insert(0, func_node.attr.value)
                func_node = func_node.value
            if isinstance(func_node, cst.Name):
                parts.insert(0, func_node.value)
            return ".".join(parts)
        return ""
