# cocotb2_migrator/transformers/join_transformer.py

import libcst as cst
from libcst import Call, Attribute, Name, Arg
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class JoinTransformer(BaseCocotbTransformer):
    name = "JoinTransformer"

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        """
        Transform Join and Task.join() calls:
        - Join(task) -> task (direct awaiting)
        - task.join() -> task (direct awaiting)
        """
        # Handle Join(task) -> task
        if isinstance(original_node.func, cst.Name) and original_node.func.value == "Join":
            if len(original_node.args) >= 1:
                task_arg = original_node.args[0]
                self.mark_modified()
                return task_arg.value

        # Handle task.join() -> task
        elif isinstance(original_node.func, cst.Attribute):
            if original_node.func.attr.value == "join":
                self.mark_modified()
                return original_node.func.value

        return updated_node

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        """
        Remove Join imports as they're no longer needed
        """
        if original_node.module:
            module_name = self.get_full_name(original_node.module)
            
            if module_name == "cocotb.triggers":
                if original_node.names and not isinstance(original_node.names, cst.ImportStar):
                    new_names = []
                    for alias in original_node.names:
                        if isinstance(alias, cst.ImportAlias):
                            if isinstance(alias.name, cst.Name) and alias.name.value == "Join":
                                # Skip Join import
                                self.mark_modified()
                                continue
                        new_names.append(alias)
                    
                    if not new_names:
                        # If no imports left, remove the entire import
                        return cst.RemovalSentinel.REMOVE
                    else:
                        return updated_node.with_changes(names=new_names)

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