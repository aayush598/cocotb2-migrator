import libcst as cst
from libcst.metadata import MetadataWrapper
from cocotb2_migrator.transformers.logicarray_transformer import LogicArrayTransformer


def apply_transformer(source: str) -> str:
    """
    Helper function to apply LogicArrayTransformer and return the transformed code.
    """
    tree = cst.parse_module(source)
    wrapper = MetadataWrapper(tree)
    transformer = LogicArrayTransformer()
    modified_tree = wrapper.visit(transformer)
    return modified_tree.code


def test_integer_attribute():
    source = "x = signal.integer"
    expected = "x = signal.to_unsigned()"
    assert apply_transformer(source) == expected


def test_signed_integer_attribute():
    source = "x = signal.signed_integer"
    expected = "x = signal.to_signed()"
    assert apply_transformer(source) == expected


def test_binstr_attribute():
    source = "x = signal.binstr"
    expected = "x = str(signal)"
    assert apply_transformer(source) == expected


def test_buff_attribute():
    source = "x = signal.buff"
    expected = "x = signal.to_bytes()"
    assert apply_transformer(source) == expected


def test_constructor_unsigned():
    source = "x = LogicArray(42)"
    expected = "x = LogicArray.from_unsigned(42)"
    assert apply_transformer(source) == expected


def test_constructor_signed():
    source = "x = LogicArray(-5)"
    expected = "x = LogicArray.from_signed(-5)"
    assert apply_transformer(source) == expected


def test_import_from_binary():
    source = "from cocotb.binary import LogicArray"
    expected = "from cocotb.types import LogicArray"
    assert apply_transformer(source) == expected


def test_import_from_cocotb():
    source = "from cocotb import LogicArray"
    expected = "from cocotb.types import LogicArray"
    assert apply_transformer(source) == expected


def test_import_unrelated():
    source = "from cocotb.clock import Clock"
    expected = "from cocotb.clock import Clock"  # Should remain unchanged
    assert apply_transformer(source) == expected


def test_constructor_with_variable():
    source = "x = LogicArray(my_var)"
    # Should remain unchanged since variable isn't an integer literal
    expected = "x = LogicArray(my_var)"
    assert apply_transformer(source) == expected
