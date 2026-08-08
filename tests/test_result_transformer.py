import libcst as cst

from cocotb2_migrator.transformers.result_transformer import ResultTransformer


def apply(src: str) -> str:
    return cst.parse_module(src).visit(ResultTransformer()).code.strip()


# ---------------------------------------------------------------------------
# Qualified cocotb.result usages
# ---------------------------------------------------------------------------


def test_raise_qualified_testsuccess_to_pass_test():
    src = "raise cocotb.result.TestSuccess('done')"
    expected = "cocotb.pass_test('done')"
    assert apply(src) == expected


def test_raise_qualified_testsuccess_no_message():
    src = "raise cocotb.result.TestSuccess()"
    expected = "cocotb.pass_test()"
    assert apply(src) == expected


def test_raise_qualified_testfailure_to_assert():
    src = "raise cocotb.result.TestFailure('boom')"
    expected = "assert False, 'boom'"
    assert apply(src) == expected


def test_raise_qualified_testerror_to_assert():
    src = "raise cocotb.result.TestError('boom')"
    expected = "assert False, 'boom'"
    assert apply(src) == expected


def test_raise_qualified_returnvalue_to_return():
    src = "raise cocotb.result.ReturnValue(42)"
    expected = "return 42"
    assert apply(src) == expected


def test_simtimeouterror_attribute_moved_to_triggers():
    src = "e = cocotb.result.SimTimeoutError"
    expected = "e = cocotb.triggers.SimTimeoutError"
    assert apply(src) == expected


def test_testcomplete_qualified_raise_warns():
    result = apply("raise cocotb.result.TestComplete()")
    assert "# WARNING: `cocotb.result.TestComplete` was removed" in result
    assert "raise cocotb.result.TestComplete()" in result


# ---------------------------------------------------------------------------
# Bare names imported from cocotb.result
# ---------------------------------------------------------------------------


def test_raise_bare_testsuccess_when_imported():
    src = "from cocotb.result import TestSuccess\nraise TestSuccess('done')"
    result = apply(src)
    assert "cocotb.pass_test('done')" in result
    assert "raise TestSuccess" not in result


def test_raise_bare_testfailure_when_imported():
    src = "from cocotb.result import TestFailure\nraise TestFailure('boom')"
    result = apply(src)
    assert "assert False, 'boom'" in result


def test_raise_bare_testsuccess_with_alias_import():
    src = "from cocotb.result import TestFailure as tf\nraise tf('boom')"
    result = apply(src)
    assert "assert False, 'boom'" in result


def test_raise_bare_not_imported_left_unchanged():
    src = "raise TestFailure('x')"
    assert apply(src) == "raise TestFailure('x')"


# ---------------------------------------------------------------------------
# raise_error / create_error
# ---------------------------------------------------------------------------


def test_qualified_raise_error_statement():
    src = "cocotb.result.raise_error('boom')"
    expected = "assert False, 'boom'"
    assert apply(src) == expected


def test_bare_raise_error_when_imported():
    src = "from cocotb.result import raise_error\nraise_error('boom')"
    result = apply(src)
    assert "assert False, 'boom'" in result


def test_bare_raise_error_not_imported_left_unchanged():
    assert apply("raise_error('boom')") == "raise_error('boom')"


def test_qualified_create_error():
    src = "err = cocotb.result.create_error('boom')"
    expected = "err = AssertionError('boom')"
    assert apply(src) == expected


def test_bare_create_error_when_imported():
    src = "from cocotb.result import create_error\nerr = create_error('boom')"
    result = apply(src)
    assert "err = AssertionError('boom')" in result


def test_create_error_in_raise_context():
    src = "raise cocotb.result.create_error('boom')"
    expected = "raise AssertionError('boom')"
    assert apply(src) == expected


# ---------------------------------------------------------------------------
# Unrelated code stays untouched
# ---------------------------------------------------------------------------


def test_unrelated_raise_untouched():
    src = "raise RuntimeError('x')"
    assert apply(src) == "raise RuntimeError('x')"
