import libcst as cst
from libcst.metadata import MetadataWrapper
from cocotb2_migrator.transformers.task_transformer import TaskTransformer


def apply_transformer(source: str) -> str:
    tree = cst.parse_module(source)
    wrapper = MetadataWrapper(tree)
    transformer = TaskTransformer()
    modified_tree = wrapper.visit(transformer)
    return modified_tree.code


def test_kill_to_cancel():
    source = "task.kill()"
    expected = "task.cancel()"
    assert apply_transformer(source) == expected


def test_has_started_removed():
    source = "task.has_started()"
    expected = '"# Task.has_started() was removed - manual intervention needed"'
    assert apply_transformer(source) == expected


def test_cocotb_start_to_start_soon():
    source = "cocotb.start(my_coro())"
    expected = "cocotb.start_soon(my_coro())"
    assert apply_transformer(source) == expected


def test_import_test_success_removed():
    source = "from cocotb.result import TestSuccess"
    expected = ""  # Import should be fully removed
    assert apply_transformer(source).strip() == expected


def test_import_with_multiple_symbols_removes_only_testsuccess():
    source = "from cocotb.result import TestSuccess, TestFailure"
    expected = "from cocotb.result import TestFailure"
    assert apply_transformer(source) == expected


def test_raise_testsuccess_to_pass_test():
    source = "raise TestSuccess()"
    expected = "cocotb.pass_test()"
    assert apply_transformer(source).strip() == expected


def test_non_testsuccess_raise_untouched():
    source = "raise TestFailure('fail')"
    expected = "raise TestFailure('fail')"
    assert apply_transformer(source) == expected


def test_irrelevant_import_untouched():
    source = "from cocotb.triggers import Timer"
    expected = "from cocotb.triggers import Timer"
    assert apply_transformer(source) == expected


def test_non_task_call_untouched():
    source = "print('hello')"
    expected = "print('hello')"
    assert apply_transformer(source) == expected
