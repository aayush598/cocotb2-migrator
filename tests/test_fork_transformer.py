from libcst import parse_module
from cocotb2_migrator.transformers.fork_transformer import ForkTransformer

def test_fork_to_start_soon():
    source = "cocotb.fork(my_task())"
    expected = "cocotb.start_soon(my_task())"
    
    tree = parse_module(source)
    modified = tree.visit(ForkTransformer())
    assert modified.code.strip() == expected
