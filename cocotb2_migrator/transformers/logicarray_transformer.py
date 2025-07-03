# cocotb2_migrator/transformers/logicarray_transformer.py

import libcst as cst
from libcst import Attribute, Call, Name, Arg
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class LogicArrayTransformer(BaseCocotbTransformer):
    name = "LogicArrayTransformer"

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        """
        Transform deprecated LogicArray attributes:
        - LogicArray.integer -> LogicArray.to_unsigned()
        - LogicArray.signed_integer -> LogicArray.to_signed()
        - LogicArray.binstr -> str(LogicArray)
        - LogicArray.buff -> LogicArray.to_bytes()
        """
        if isinstance(original_node.attr, cst.Name):
            attr_name = original_node.attr.value
            
            if attr_name == "integer":
                # LogicArray.integer -> LogicArray.to_unsigned()
                self.mark_modified()
                return cst.Call(
                    func=cst.Attribute(
                        value=original_node.value,
                        attr=cst.Name("to_unsigned")
                    ),
                    args=[]
                )
            
            elif attr_name == "signed_integer":
                # LogicArray.signed_integer -> LogicArray.to_signed()
                self.mark_modified()
                return cst.Call(
                    func=cst.Attribute(
                        value=original_node.value,
                        attr=cst.Name("to_signed")
                    ),
                    args=[]
                )
            
            elif attr_name == "binstr":
                # LogicArray.binstr -> str(LogicArray)
                self.mark_modified()
                return cst.Call(
                    func=cst.Name("str"),
                    args=[cst.Arg(value=original_node.value)]
                )
            
            elif attr_name == "buff":
                # LogicArray.buff -> LogicArray.to_bytes()
                self.mark_modified()
                return cst.Call(
                    func=cst.Attribute(
                        value=original_node.value,
                        attr=cst.Name("to_bytes")
                    ),
                    args=[]
                )

        return updated_node

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        """
        Transform LogicArray constructor calls:
        - LogicArray(int_value) -> LogicArray.from_unsigned(int_value)
        - LogicArray(negative_int) -> LogicArray.from_signed(negative_int)
        """
        if isinstance(original_node.func, cst.Name) and original_node.func.value == "LogicArray":
            if len(original_node.args) >= 1:
                first_arg = original_node.args[0]
                int_value_node = first_arg.value

                # Handle negative integer literals like -5
                if isinstance(int_value_node, cst.UnaryOperation) and isinstance(int_value_node.operator, cst.Minus) and isinstance(int_value_node.expression, cst.Integer):
                    self.mark_modified()
                    return cst.Call(
                        func=cst.Attribute(
                            value=cst.Name("LogicArray"),
                            attr=cst.Name("from_signed")
                        ),
                        args=list(updated_node.args)
                    )

                # Handle positive integer literals like 42
                if isinstance(int_value_node, cst.Integer):
                    self.mark_modified()
                    return cst.Call(
                        func=cst.Attribute(
                            value=cst.Name("LogicArray"),
                            attr=cst.Name("from_unsigned")
                        ),
                        args=list(updated_node.args)
                    )

        return updated_node

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        """
        Update LogicArray imports to use cocotb.types
        """
        if original_node.module:
            module_name = self.get_full_name(original_node.module)
            
            # Update imports from old locations to cocotb.types
            if module_name in ["cocotb.binary", "cocotb"]:
                if original_node.names and not isinstance(original_node.names, cst.ImportStar):
                    # Check if LogicArray is being imported
                    for alias in original_node.names:
                        if isinstance(alias, cst.ImportAlias):
                            if isinstance(alias.name, cst.Name) and alias.name.value == "LogicArray":
                                self.mark_modified()
                                return updated_node.with_changes(
                                    module=cst.Attribute(
                                        value=cst.Name("cocotb"),
                                        attr=cst.Name("types")
                                    )
                                )

        return updated_node

    def get_full_name(self, module: cst.BaseExpression) -> str:
        """
        Utility to extract full dotted name from module expression
        """
        if isinstance(module, cst.Name):
            return module.value
        elif isinstance(module, cst.Attribute):
            parts = []
            while isinstance(module, cst.Attribute):
                parts.append(module.attr.value)
                module = module.value
            if isinstance(module, cst.Name):
                parts.append(module.value)
            return ".".join(reversed(parts))
        return ""