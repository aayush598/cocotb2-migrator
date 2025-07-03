import libcst as cst
from cocotb2_migrator.transformers.join_transformer import JoinTransformer


def apply_transformer(transformer_class, source: str) -> str:
    tree = cst.parse_module(source)
    wrapper = cst.MetadataWrapper(tree)
    transformer = transformer_class()
    modified_tree = wrapper.visit(transformer)
    return modified_tree.code


def test_join_function_call_transformed():
    src = """
from cocotb.triggers import Join

async def test_something():
    task = some_coro()
    await Join(task)
"""
    expected = """
async def test_something():
    task = some_coro()
    await task
"""
    assert apply_transformer(JoinTransformer, src).strip() == expected.strip()


def test_task_dot_join_transformed():
    src = """
async def test_something():
    task = some_coro()
    await task.join()
"""
    expected = """
async def test_something():
    task = some_coro()
    await task
"""
    assert apply_transformer(JoinTransformer, src).strip() == expected.strip()


def test_remove_import_only_join():
    src = """
from cocotb.triggers import Join

async def test():
    await Join(task)
"""
    expected = """
async def test():
    await task
"""
    assert apply_transformer(JoinTransformer, src).strip() == expected.strip()


def test_remove_join_keep_others():
    src = """
from cocotb.triggers import Join, RisingEdge

async def test():
    await Join(task)
"""
    expected = """
from cocotb.triggers import RisingEdge

async def test():
    await task
"""
    assert apply_transformer(JoinTransformer, src).strip() == expected.strip()


def test_preserve_unrelated_imports():
    src = """
from cocotb.triggers import RisingEdge

async def test():
    await RisingEdge(clk)
"""
    expected = """
from cocotb.triggers import RisingEdge

async def test():
    await RisingEdge(clk)
"""
    assert apply_transformer(JoinTransformer, src).strip() == expected.strip()
