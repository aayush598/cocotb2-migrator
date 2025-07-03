import libcst as cst
from cocotb2_migrator.transformers.clock_transformer import ClockTransformer


def transform_code(source: str) -> str:
    module = cst.parse_module(source)
    transformer = ClockTransformer()
    modified = module.visit(transformer)
    return modified.code


def test_rename_units_to_unit():
    src = "Clock(sig, 10, units='ns')"
    expected = "Clock(sig, 10, unit='ns')"
    assert transform_code(src) == expected


def test_remove_cycles_argument():
    src = "clk.start(cycles=10)"
    expected = "clk.start()"
    assert transform_code(src) == expected


def test_pass_through_non_cycles_args():
    src = "clk.start(delay=5)"
    expected = "clk.start(delay=5)"
    assert transform_code(src) == expected


def test_cocotb_start_soon_removed():
    src = "cocotb.start_soon(clk.start())"
    expected = "clk.start()"
    assert transform_code(src) == expected


def test_non_matching_start_soon_left_unchanged():
    src = "cocotb.start_soon(other_func())"
    expected = "cocotb.start_soon(other_func())"
    assert transform_code(src) == expected


def test_remove_frequency_attribute():
    src = "clk.frequency"
    expected = '"# Clock.frequency was removed - manual intervention needed"'
    assert transform_code(src) == expected


def test_unrelated_code_unchanged():
    src = "print('hello')"
    expected = "print('hello')"
    assert transform_code(src) == expected
