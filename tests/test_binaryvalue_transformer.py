from libcst import parse_module
from cocotb2_migrator.transformers.binaryvalue_transformer import BinaryValueTransformer

def test_binaryvalue_module_path_update():
    source = "val = cocotb.binary.BinaryValue('1010')"
    expected = "val = cocotb.BinaryValue('1010')"
    tree = parse_module(source)
    modified = tree.visit(BinaryValueTransformer())
    assert modified.code.strip() == expected

def test_binaryvalue_kwarg_update():
    source = "val = cocotb.BinaryValue('1010', bigEndian=True)"
    expected = "val = cocotb.BinaryValue('1010', big_endian=True)"
    tree = parse_module(source)
    modified = tree.visit(BinaryValueTransformer())
    assert modified.code.strip() == expected
