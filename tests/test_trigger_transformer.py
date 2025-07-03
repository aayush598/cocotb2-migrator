# tests/test_trigger_transformer.py

import unittest
import libcst as cst
from cocotb2_migrator.transformers.join_transformer import TriggerTransformer

class TestTriggerTransformer(unittest.TestCase):

    def transform(self, code: str) -> str:
        module = cst.parse_module(code)
        wrapper = module.visit(TriggerTransformer())
        return wrapper.code

    def test_rising_edge(self):
        before = "RisingEdge(clk)"
        after = "cocotb.triggers.RisingEdge(clk)"
        self.assertEqual(self.transform(before), after)

    def test_falling_edge(self):
        before = "FallingEdge(sig)"
        after = "cocotb.triggers.FallingEdge(sig)"
        self.assertEqual(self.transform(before), after)

    def test_nested_attribute(self):
        # Should not change if already qualified
        code = "cocotb.triggers.RisingEdge(clk)"
        self.assertEqual(self.transform(code), code)
