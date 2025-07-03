import tempfile
from pathlib import Path

import pytest
import libcst as cst

from cocotb2_migrator.parser import TransformerPipeline, parse_and_transform_file


# Sample transformer that changes @cocotb.coroutine to async def
class DummyCoroutineTransformer(cst.CSTTransformer):
    def leave_FunctionDef(self, original_node, updated_node):
        if original_node.decorators:
            for decorator in original_node.decorators:
                if (
                    isinstance(decorator.decorator, cst.Attribute)
                    and decorator.decorator.attr.value == "coroutine"
                ):
                    return updated_node.with_changes(
                        asynchronous=cst.Asynchronous(
                            whitespace_after=cst.SimpleWhitespace(" ")
                        ),
                        decorators=[
                            d for d in updated_node.decorators
                            if not (
                                isinstance(d.decorator, cst.Attribute)
                                and d.decorator.attr.value == "coroutine"
                            )
                        ]
                    )

        return updated_node


def test_transformer_pipeline_applies_transformation():
    input_code = """
import cocotb
@cocotb.coroutine
def test_example():
    yield Timer(10)
"""
    expected_output_contains = "async def test_example():"

    pipeline = TransformerPipeline([DummyCoroutineTransformer])
    output_code, applied = pipeline.apply(input_code)

    assert "DummyCoroutineTransformer" in applied
    assert expected_output_contains in output_code


def test_parse_and_transform_file_in_place(tmp_path: Path):
    input_code = """
import cocotb
@cocotb.coroutine
def test_example():
    yield Timer(10)
"""
    file_path = tmp_path / "test_file.py"
    file_path.write_text(input_code)

    parse_and_transform_file(str(file_path), [DummyCoroutineTransformer], in_place=True, show_diff=False)

    modified_code = file_path.read_text()
    assert "async def test_example():" in modified_code
    assert "@cocotb.coroutine" not in modified_code


def test_parse_and_transform_file_preview(tmp_path: Path, capsys):
    input_code = """
import cocotb
@cocotb.coroutine
def test_example():
    yield Timer(10)
"""
    file_path = tmp_path / "test_file_preview.py"
    file_path.write_text(input_code)

    parse_and_transform_file(str(file_path), [DummyCoroutineTransformer], in_place=False, show_diff=True)
    captured = capsys.readouterr()

    assert "async def test_example():" in captured.out
    assert "Transformations applied" in captured.out
