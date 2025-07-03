import json
from collections import defaultdict

class MigrationReport:
    def __init__(self):
        self._report = {}

    def add(self, file_path: str, applied_transformers: list[str]):
        self._report[file_path] = applied_transformers

    def save(self, file_path: str):
        import json
        with open(file_path, 'w') as f:
            json.dump(self._report, f, indent=2)

    def print(self):
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Migration Report")
        table.add_column("File", style="cyan")
        table.add_column("Transformations Applied", style="green")

        for file_path, transformations in self._report.items():
            table.add_row(file_path, ", ".join(transformations))

        console.print(table)

    def to_dict(self):
        return self._report
