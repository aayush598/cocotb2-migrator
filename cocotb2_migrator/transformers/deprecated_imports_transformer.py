import libcst as cst
from libcst import ImportFrom, ImportAlias, Name, Attribute
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class DeprecatedImportsTransformer(BaseCocotbTransformer):
    name = "DeprecatedImportsTransformer"

    def leave_ImportFrom(self, original_node: ImportFrom, updated_node: ImportFrom) -> cst.ImportFrom:
        """
        Update deprecated imports:
        - cocotb.decorators -> cocotb
        - cocotb.result -> cocotb
        - cocotb.regression -> REMOVE (no longer needed)
        """
        if original_node.module:
            module_name = self.get_full_name(original_node.module)

            if module_name == "cocotb.decorators":
                self.mark_modified()
                return updated_node.with_changes(
                    module=Name("cocotb")
                )

            elif module_name == "cocotb.result":
                self.mark_modified()
                return updated_node.with_changes(
                    module=Name("cocotb")
                )

            elif module_name == "cocotb.regression":
                self.mark_modified()
                # Remove the whole import
                return cst.RemoveFromParent()

        return updated_node

    def get_full_name(self, module: cst.BaseExpression) -> str:
        """
        Utility to extract full dotted name from module expression
        """
        if isinstance(module, Name):
            return module.value
        elif isinstance(module, Attribute):
            parts = []
            while isinstance(module, Attribute):
                parts.append(module.attr.value)
                module = module.value
            if isinstance(module, Name):
                parts.append(module.value)
            return ".".join(reversed(parts))
        return ""
