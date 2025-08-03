from libcst import parse_module
from cocotb2_migrator.transformers.binaryvalue_transformer import BinaryValueTransformer

def apply_transformation(source: str) -> str:
    tree = parse_module(source)
    transformer = BinaryValueTransformer()
    modified = tree.visit(transformer)
    result = modified.code.strip()
    return result

def test_binaryvalue_module_path_update():
    source = "val = cocotb.binary.BinaryValue('1010')"
    expected = "val = cocotb.types.LogicArray('1010')"
    assert apply_transformation(source) == expected

def test_binaryvalue_kwarg_update():
    source = "val = cocotb.BinaryValue('1010', bigEndian=True)"
    expected = 'val = LogicArray.from_bytes(\'1010\', byteorder="big")'
    assert apply_transformation(source) == expected

def test_binaryvalue_from_unsigned():
    source = "val = BinaryValue(42, 8)"
    expected = "val = LogicArray.from_unsigned(42, 8)"
    assert apply_transformation(source) == expected

def test_binaryvalue_from_signed():
    source = "val = BinaryValue(42, 8, binaryRepresentation=BinaryRepresentation.SIGNED)"
    expected = "val = LogicArray.from_signed(42, 8)"
    assert apply_transformation(source) == expected

def test_binaryvalue_no_signed_magnitude_no_warning():
    """Test that no warning is added when SIGNED_MAGNITUDE is not used"""
    source = "val = BinaryValue(42, 8)"
    result = apply_transformation(source)
    
    # Should not contain warning
    assert "# WARNING: BinaryRepresentation.SIGNED_MAGNITUDE has no LogicArray equivalent" not in result
    # Should contain the transformed code
    assert "val = LogicArray.from_unsigned(42, 8)" in result

def test_binaryvalue_from_bytes_big_endian():
    source = 'val = BinaryValue(b"\\xAA", bigEndian=True)'
    expected = 'val = LogicArray.from_bytes(b"\\xAA", byteorder="big")'
    assert apply_transformation(source) == expected

def test_binaryvalue_from_bytes_little_endian():
    source = 'val = BinaryValue(b"\\xBB", bigEndian=False)'
    expected = 'val = LogicArray.from_bytes(b"\\xBB", byteorder="little")'
    assert apply_transformation(source) == expected

def test_property_integer_to_unsigned():
    source = "x = val.integer"
    expected = "x = val.to_unsigned()"
    assert apply_transformation(source) == expected

def test_property_signed_integer():
    source = "x = val.signed_integer"
    expected = "x = val.to_signed()"
    assert apply_transformation(source) == expected

def test_property_binstr():
    source = "x = val.binstr"
    expected = "x = str(val)"
    assert apply_transformation(source) == expected

def test_property_buff():
    source = "x = val.buff"
    expected = 'x = val.to_bytes(byteorder="big")'
    assert apply_transformation(source) == expected

def test_default_case():
    source = "val = BinaryValue('1010')"
    expected = "val = LogicArray('1010')"
    assert apply_transformation(source) == expected