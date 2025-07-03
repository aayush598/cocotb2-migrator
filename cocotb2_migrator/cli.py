import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Cocotb 1.x to 2.x migration tool")
    parser.add_argument("path", type=str, help="Path to the project directory")
    parser.add_argument("--report", type=str, help="Path to save the migration report (optional)")
    return parser.parse_args()
