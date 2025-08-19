# cocotb2_migrator/transformers/clock_transformer.py

import libcst as cst
from libcst import Call, Attribute, Name
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class ClockTransformer(BaseCocotbTransformer):
    """
    Transforms cocotb.clock.Clock usage according to cocotb 2.0 migration guide.

    Key transformations:
    1. cocotb.start_soon(clock.start()) -> clock.start()
    2. Clock(..., units="ns") -> Clock(..., unit="ns")
    3. clk.start(cycles=...) -> clk.start()
    4. Clock.frequency -> WARNING comment (no direct replacement)
    """
    name = "ClockTransformer"

    def __init__(self):
        super().__init__()
        self.frequency_found = False
        self.cycles_found = False

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

        # Transform: Clock(..., units=...) -> Clock(..., unit=...)
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
                cycles_removed = False
                for arg in original_node.args:
                    if arg.keyword and arg.keyword.value == "cycles":
                        self.mark_modified()
                        cycles_removed = True
                        continue
                    new_args.append(arg)

                if new_args != list(original_node.args):
                    self.cycles_found = True
                    return updated_node.with_changes(args=new_args)

        return updated_node

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        """
        Transform deprecated Clock attributes:
        - Clock.frequency -> WARNING (manual intervention needed)
        """
        if isinstance(original_node.attr, cst.Name) and original_node.attr.value == "frequency":
            self.frequency_found = True
            self.mark_modified()
        return updated_node

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Add warning comment at the top if Clock.frequency was found"""
        warnings = []
        if self.frequency_found:
            warnings.append("# WARNING: Clock.frequency was removed in cocotb 2.0 (manual fix required)")
        if self.cycles_found:
            warnings.append("# WARNING: Clock.start(cycles=...) was removed in cocotb 2.0 (manual fix required)")

        if warnings:
        # Insert warnings as top-level comments
            new_body = [
                cst.EmptyLine(comment=cst.Comment(w)) for w in warnings
            ] + list(updated_node.body)
            return updated_node.with_changes(body=new_body)
        return updated_node
