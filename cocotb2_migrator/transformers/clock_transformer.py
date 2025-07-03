# cocotb2_migrator/transformers/clock_transformer.py

import libcst as cst
from libcst import Call, Attribute, Name, Arg
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class ClockTransformer(BaseCocotbTransformer):
    name = "ClockTransformer"

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        # Transform: cocotb.start_soon(clock.start()) -> clock.start()
        if isinstance(original_node.func, cst.Attribute):
            if (isinstance(original_node.func.value, cst.Name) and 
                original_node.func.value.value == "cocotb" and
                original_node.func.attr.value == "start_soon"):
                
                if len(original_node.args) == 1:
                    arg = original_node.args[0]
                    if isinstance(arg.value, cst.Call):
                        call = arg.value
                        if isinstance(call.func, cst.Attribute) and call.func.attr.value == "start":
                            self.mark_modified()
                            return call

        # Transform: Clock(...) with units -> unit
        if isinstance(original_node.func, cst.Name) and original_node.func.value == "Clock":
            new_args = []
            for arg in original_node.args:
                if arg.keyword and arg.keyword.value == "units":
                    new_args.append(arg.with_changes(keyword=cst.Name("unit")))
                    self.mark_modified()
                else:
                    new_args.append(arg)

            if new_args != list(original_node.args):
                return updated_node.with_changes(args=new_args)

        # Transform: clk.start(cycles=...) -> clk.start()
        if isinstance(original_node.func, cst.Attribute):
            if original_node.func.attr.value == "start":
                new_args = []
                for arg in original_node.args:
                    if arg.keyword and arg.keyword.value == "cycles":
                        self.mark_modified()
                        continue
                    new_args.append(arg)

                if new_args != list(original_node.args):
                    return updated_node.with_changes(args=new_args)

        return updated_node

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        """
        Transform deprecated Clock attributes:
        - Clock.frequency -> (removed, no direct replacement)
        """
        if isinstance(original_node.attr, cst.Name) and original_node.attr.value == "frequency":
            # Clock.frequency was removed - this needs manual intervention
            # We'll add a comment to indicate this
            self.mark_modified()
            return cst.SimpleString('"# Clock.frequency was removed - manual intervention needed"')

        return updated_node