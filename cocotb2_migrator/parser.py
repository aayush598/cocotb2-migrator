import os
from pathlib import Path
from typing import List, Optional, Tuple, Type

import libcst as cst
from libcst import Module, CSTTransformer
from rich.console import Console
from rich.syntax import Syntax

console = Console()


class TransformerPipeline:
    """
    Runs a sequence of CSTTransformer subclasses on a file.
    """

    def __init__(self, transformers: List[Type[CSTTransformer]]):
        self.transformers = transformers

    def apply(self, source_code: str, file_path: Optional[str] = None) -> Tuple[str, List[str]]:
        """
        Applies all transformers in sequence to the source code.

        Returns:
            Tuple[str, List[str]]: (transformed_code, list_of_applied_transformers)
        """
        module: Module = cst.parse_module(source_code)
        applied = []

        for transformer_cls in self.transformers:
            transformer = transformer_cls()
            modified = module.visit(transformer)

            if modified.code != module.code:
                applied.append(transformer_cls.__name__)
                module = modified

        return module.code, applied


def load_file(file_path: str) -> str:
    """
    Reads and returns the content of the given file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' does not exist.")
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def save_file(file_path: str, content: str):
    """
    Overwrites the file with transformed content.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def parse_and_transform_file(
    file_path: str,
    transformers: List[Type[CSTTransformer]],
    in_place: bool = False,
    show_diff: bool = True
) -> Tuple[Optional[str], List[str]]:
    """
    Parses and applies transformers to the file at `file_path`.
    If `in_place` is True, updates the file with transformed code.
    Returns the transformed code and list of applied transformers.
    """
    source = load_file(file_path)
    pipeline = TransformerPipeline(transformers)
    transformed_code, applied_transformers = pipeline.apply(source, file_path)

    if not applied_transformers:
        console.print(f"[yellow]No transformations applied to [bold]{file_path}[/bold][/yellow]")
        return None, []

    if show_diff:
        console.rule(f"[bold cyan]Transformations applied: {', '.join(applied_transformers)}")
        console.print(Syntax(transformed_code, "python", theme="monokai", line_numbers=True))

    if in_place:
        save_file(file_path, transformed_code)
        console.print(f"[green]Updated [bold]{file_path}[/bold] with transformations.[/green]")
    else:
        console.print(f"[blue]Preview only. Use '--in-place' to write changes to file.[/blue]")

    return transformed_code, applied_transformers
