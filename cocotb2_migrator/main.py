from cocotb2_migrator.cli import parse_args
from cocotb2_migrator.migrator import migrate_directory
from cocotb2_migrator.report import MigrationReport

def main():
    args = parse_args()
    report = MigrationReport()
    migrate_directory(args.path, report)
    if args.report:
        report.save(args.report)
    else:
        report.print()