import libcst as cst

from cocotb2_migrator.transformers.task_transformer import TaskTransformer


def apply_transformer(source: str) -> str:
    tree = cst.parse_module(source)
    return tree.visit(TaskTransformer()).code


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


def test_non_task_call_untouched():
    source = "other.call()"
    expected = "other.call()"
    assert apply_transformer(source) == expected


def test_irrelevant_import_untouched():
    source = "from cocotb.triggers import Timer"
    expected = "from cocotb.triggers import Timer"
    assert apply_transformer(source) == expected
