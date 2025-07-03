# cocotb2_migrator/transformers/task_transformer.py

import libcst as cst
from libcst import Call, Attribute, Name, Arg
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class TaskTransformer(BaseCocotbTransformer):
    name = "TaskTransformer"

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        """
        Transform Task-related method calls:
        - Task.kill() -> Task.cancel()
        - Task.has_started() -> (removed, no direct replacement)
        - cocotb.start() -> cocotb.start_soon()
        """
        if isinstance(original_node.func, cst.Attribute):
            attr_name = original_node.func.attr.value
            
            # Transform Task.kill() -> Task.cancel()
            if attr_name == "kill":
                self.mark_modified()
                return updated_node.with_changes(
                    func=original_node.func.with_changes(attr=cst.Name("cancel"))
                )
            
            # Transform Task.has_started() -> remove (needs manual intervention)
            elif attr_name == "has_started":
                self.mark_modified()
                return cst.SimpleString('"# Task.has_started() was removed - manual intervention needed"')
            
            # Transform cocotb.start() -> cocotb.start_soon()
            elif (isinstance(original_node.func.value, cst.Name) and 
                  original_node.func.value.value == "cocotb" and
                  attr_name == "start"):
                self.mark_modified()
                return updated_node.with_changes(
                    func=original_node.func.with_changes(attr=cst.Name("start_soon"))
                )

        return updated_node

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        """
        Update Task-related imports:
        - TestSuccess -> remove (use cocotb.pass_test() instead)
        """
        if original_node.module:
            module_name = self.get_full_name(original_node.module)
            
            if module_name == "cocotb.result":
                if original_node.names and not isinstance(original_node.names, cst.ImportStar):
                    new_names = []
                    for alias in original_node.names:
                        if isinstance(alias, cst.ImportAlias):
                            if isinstance(alias.name, cst.Name) and alias.name.value == "TestSuccess":
                                # Skip TestSuccess import
                                self.mark_modified()
                                continue
                        new_names.append(alias)
                    
                    if not new_names:
                        # If no imports left, remove the entire import
                        return cst.RemovalSentinel.REMOVE
                    else:
                        return updated_node.with_changes(names=new_names)

        return updated_node

    def leave_Raise(self, original_node: cst.Raise, updated_node: cst.Raise) -> cst.BaseStatement:
        """
        Transform raise TestSuccess() -> cocotb.pass_test()
        """
        if original_node.exc:
            if isinstance(original_node.exc, cst.Call):
                if isinstance(original_node.exc.func, cst.Name) and original_node.exc.func.value == "TestSuccess":
                    self.mark_modified()
                    # Replace with an expression statement calling cocotb.pass_test()
                    return cst.Expr(
                        value=cst.Call(
                            func=cst.Attribute(
                                value=cst.Name("cocotb"),
                                attr=cst.Name("pass_test")
                            ),
                            args=[]
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