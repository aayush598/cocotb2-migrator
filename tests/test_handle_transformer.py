from libcst import parse_module
from cocotb2_migrator.transformers.handle_transformer import HandleTransformer

def test_get_value_removed():
    source = "val = sig.value.get_value()"
    expected = "val = sig.value"
    mod = parse_module(source).visit(HandleTransformer())
    assert mod.code.strip() == expected

def test_integer_to_int():
    source = "i = sig.value.integer"
    expected = "i = int(sig.value)"
    mod = parse_module(source).visit(HandleTransformer())
    assert mod.code.strip() == expected

def test_binstr_to_format():
    source = "b = sig.value.binstr"
    expected = "b = format(sig.value, 'b')"
    mod = parse_module(source).visit(HandleTransformer())
    assert mod.code.strip() == expected

def test_raw_value_removed():
    source = "r = sig.value.raw_value"
    expected = "r = sig.value"
    mod = parse_module(source).visit(HandleTransformer())
    assert mod.code.strip() == expected
