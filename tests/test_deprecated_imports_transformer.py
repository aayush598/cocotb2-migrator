from libcst import parse_module

from cocotb2_migrator.transformers.deprecated_imports_transformer import (
    DeprecatedImportsTransformer,
)


def apply(src: str) -> str:
    mod = parse_module(src).visit(DeprecatedImportsTransformer())
    return mod.code.strip()


# ---------------------------------------------------------------------------
# cocotb.decorators
# ---------------------------------------------------------------------------


def test_decorators_coroutine_import_migrated():
    src = "from cocotb.decorators import coroutine"
    expected = "from cocotb import coroutine"
    assert apply(src) == expected


def test_decorators_test_import_migrated():
    src = "from cocotb.decorators import test"
    expected = "from cocotb import test"
    assert apply(src) == expected


def test_decorators_external_import_migrated_with_alias():
    src = "from cocotb.decorators import external"
    expected = "from cocotb.task import bridge as external"
    assert apply(src) == expected


def test_decorators_function_import_migrated_with_alias():
    src = "from cocotb.decorators import function"
    expected = "from cocotb.task import resume as function"
    assert apply(src) == expected


def test_decorators_external_preserves_explicit_alias():
    src = "from cocotb.decorators import external as ext"
    expected = "from cocotb.task import bridge as ext"
    assert apply(src) == expected


def test_decorators_public_import_removed():
    result = apply("from cocotb.decorators import public")
    assert "from cocotb.decorators import public" not in result
    assert "# WARNING: `public` was removed in cocotb 2.0" in result


def test_decorators_mixed_imports_split_across_modules():
    src = "from cocotb.decorators import coroutine, external"
    result = apply(src)
    assert "from cocotb import coroutine" in result
    assert "from cocotb.task import bridge as external" in result


# ---------------------------------------------------------------------------
# cocotb.result
# ---------------------------------------------------------------------------


def test_result_testsuccess_import_removed():
    src = "from cocotb.result import TestSuccess"
    assert apply(src) == ""


def test_result_testfailure_import_removed():
    src = "from cocotb.result import TestFailure"
    assert apply(src) == ""


def test_result_simtimeouterror_import_migrated():
    src = "from cocotb.result import SimTimeoutError"
    expected = "from cocotb.triggers import SimTimeoutError"
    assert apply(src) == expected


def test_result_testcomplete_import_removed():
    result = apply("from cocotb.result import TestComplete")
    assert "from cocotb.result import TestComplete" not in result
    assert "# WARNING: `TestComplete` was removed in cocotb 2.0" in result


def test_result_mixed_imports_migrate_and_remove():
    src = "from cocotb.result import TestFailure, SimTimeoutError"
    result = apply(src)
    assert "from cocotb.triggers import SimTimeoutError" in result
    assert "TestFailure" not in result


# ---------------------------------------------------------------------------
# cocotb.regression & plain imports
# ---------------------------------------------------------------------------


def test_regression_import_removed():
    src = "from cocotb.regression import TestFactory"
    assert apply(src) == ""


def test_plain_import_cocotb_result_removed():
    result = apply("import cocotb.result")
    assert not result.startswith("import cocotb.result")
    assert "# WARNING: `import cocotb.result` was removed" in result


def test_non_deprecated_import_untouched():
    src = "import os"
    assert apply(src) == "import os"


def test_from_cocotb_import_untouched():
    src = "from cocotb.triggers import Timer"
    assert apply(src) == "from cocotb.triggers import Timer"


# ---------------------------------------------------------------------------
# Warnings are rendered as top-of-file comments
# ---------------------------------------------------------------------------


def test_warning_comment_inserted_for_public():
    result = parse_module("from cocotb.decorators import public").visit(
        DeprecatedImportsTransformer()
    ).code
    assert "# WARNING: `public` was removed in cocotb 2.0" in result


def test_warning_comment_inserted_for_testcomplete():
    result = parse_module("from cocotb.result import TestComplete").visit(
        DeprecatedImportsTransformer()
    ).code
    assert "# WARNING: `TestComplete` was removed in cocotb 2.0" in result
