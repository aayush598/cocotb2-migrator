import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cocotb2_migrator.main import main

if __name__ == "__main__":
    main()
