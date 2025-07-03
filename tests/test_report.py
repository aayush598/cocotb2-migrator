import tempfile
import json
from cocotb2_migrator.report import MigrationReport

def test_report_saving():
    report = MigrationReport()
    report.add("example.py", "CoroutineTransformer")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmpfile:
        report.save(tmpfile.name)
        tmpfile.close()

        with open(tmpfile.name, "r") as f:
            data = json.load(f)
            assert "example.py" in data
            assert "CoroutineTransformer" in data["example.py"]
