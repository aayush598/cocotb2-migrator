from libcst import parse_module

from cocotb2_migrator.transformers.coroutine_transformer import (
    CoroutineToAsyncTransformer,
)


def apply(src: str) -> str:
    return parse_module(src).visit(CoroutineToAsyncTransformer()).code.strip()


def test_coroutine_to_async_transform():
    source = (
        "import cocotb\n\n"
        "@cocotb.test()\n"
        "@cocotb.coroutine\n"
        "def my_coro(dut):\n"
        "    yield Timer(10)\n"
    )
    expected = (
        "import cocotb\n\n"
        "@cocotb.test()\n"
        "async def my_coro(dut):\n"
        "    yield Timer(10)\n"
    )
    assert apply(source) == expected.strip()


def test_decorators_coroutine_to_async_transform():
    source = (
        "@cocotb.decorators.coroutine\n"
        "def my_coro(dut):\n"
        "    yield Timer(10)\n"
    )
    expected = (
        "async def my_coro(dut):\n"
        "    yield Timer(10)\n"
    )
    assert apply(source) == expected.strip()


def test_decorators_coroutine_call_form_to_async_transform():
    source = (
        "@cocotb.decorators.coroutine()\n"
        "def my_coro(dut):\n"
        "    yield Timer(10)\n"
    )
    expected = (
        "async def my_coro(dut):\n"
        "    yield Timer(10)\n"
    )
    assert apply(source) == expected.strip()


def test_non_coroutine_decorator_left_unchanged():
    source = (
        "@cocotb.test()\n"
        "def my_test(dut):\n"
        "    pass\n"
    )
    assert apply(source) == source.strip()
