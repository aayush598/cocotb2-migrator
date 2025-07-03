# cocotb2_migrator/migrator.py
import libcst as cst
from cocotb2_migrator.parser import parse_and_transform_file
from cocotb2_migrator.report import MigrationReport
from cocotb2_migrator.transformers.binaryvalue_transformer import BinaryValueTransformer
from cocotb2_migrator.transformers.clock_transformer import ClockTransformer
from cocotb2_migrator.transformers.coroutine_transformer import CoroutineToAsyncTransformer
from cocotb2_migrator.transformers.deprecated_imports_transformer import DeprecatedImportsTransformer
from cocotb2_migrator.transformers.environment_transformer import EnvironmentTransformer
from cocotb2_migrator.transformers.fork_transformer import ForkTransformer
from cocotb2_migrator.transformers.handle_transformer import HandleTransformer
from cocotb2_migrator.transformers.join_transformer import JoinTransformer
from cocotb2_migrator.transformers.logicarray_transformer import LogicArrayTransformer
from cocotb2_migrator.transformers.task_transformer import TaskTransformer
import os

ALL_TRANSFORMERS = [
    BinaryValueTransformer,
    ClockTransformer,
    CoroutineToAsyncTransformer,
    DeprecatedImportsTransformer,
    EnvironmentTransformer,
    ForkTransformer,
    HandleTransformer,
    JoinTransformer,
    LogicArrayTransformer,
    TaskTransformer,
]

def migrate_file(file_path: str, report: dict):
    transformed_code, applied = parse_and_transform_file(
        file_path,
        transformers=ALL_TRANSFORMERS,
        in_place=True,
        show_diff=True
    )
    if applied:
        report.add(file_path, applied)



def migrate_directory(path: str, report: dict):
    for dirpath, _, filenames in os.walk(path):
        for file in filenames:
            if file.endswith(".py"):
                filepath = os.path.join(dirpath, file)
                migrate_file(filepath, report)