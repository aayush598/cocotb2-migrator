# cocotb2_migrator/transformers/task_transformer.py

import libcst as cst

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
                return cst.SimpleString(
                    '"# Task.has_started() was removed - manual intervention needed"'
                )

            # Transform cocotb.start() -> cocotb.start_soon()
            elif (
                isinstance(original_node.func.value, cst.Name)
                and original_node.func.value.value == "cocotb"
                and attr_name == "start"
            ):
                self.mark_modified()
                return updated_node.with_changes(
                    func=original_node.func.with_changes(attr=cst.Name("start_soon"))
                )

        return updated_node
