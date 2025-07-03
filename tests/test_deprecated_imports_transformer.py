from libcst import parse_module
from cocotb2_migrator.transformers.deprecated_imports_transformer import DeprecatedImportsTransformer

def test_decorators_import_migrated():
    src = "from cocotb.decorators import coroutine"
    expected = "from cocotb import coroutine"
    mod = parse_module(src).visit(DeprecatedImportsTransformer())
    assert mod.code.strip() == expected

def test_result_import_migrated():
    src = "from cocotb.result import TestFailure"
    expected = "from cocotb import TestFailure"
    mod = parse_module(src).visit(DeprecatedImportsTransformer())
    assert mod.code.strip() == expected

def test_regression_import_removed():
    src = "from cocotb.regression import TestFactory"
    expected = ""
    mod = parse_module(src).visit(DeprecatedImportsTransformer())
    assert mod.code.strip() == expected
