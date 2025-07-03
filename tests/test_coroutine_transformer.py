from libcst import parse_module
from cocotb2_migrator.transformers.coroutine_transformer import CoroutineToAsyncTransformer

def test_coroutine_to_async_transform():
    source = '''
import cocotb

@cocotb.test()
@cocotb.coroutine
def my_coro(dut):
    yield Timer(10)
'''
    expected = '''
import cocotb

@cocotb.test()
async def my_coro(dut):
    yield Timer(10)
'''

    tree = parse_module(source)
    wrapper = tree.visit(CoroutineToAsyncTransformer())
    assert wrapper.code.strip() == expected.strip()
