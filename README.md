# cocotb2-migrator

A comprehensive tool for migrating cocotb 1.x testbenches to cocotb 2.x with async/await syntax and modern Python practices.

## Overview

cocotb2-migrator automates the migration of cocotb testbenches from version 1.x to 2.x by applying a series of code transformations. The tool handles the most common migration patterns including coroutine decorators, fork operations, handle access patterns, binary value usage, and deprecated imports.

## Features

- **Coroutine to Async/Await**: Converts `@cocotb.coroutine` decorated functions to `async def`
- **Fork to Start Soon**: Transforms `cocotb.fork()` calls to `cocotb.start_soon()`
- **Handle Access Modernization**: Updates deprecated handle value access patterns
- **Binary Value Updates**: Migrates `cocotb.binary.BinaryValue` to `cocotb.BinaryValue`
- **Import Cleanup**: Removes or updates deprecated import statements
- **Comprehensive Reporting**: Generates detailed migration reports in JSON or console format
- **In-place Transformation**: Safely updates files with syntax highlighting and diff display

## Installation

### From PyPI (Recommended)

```bash
pip install cocotb2-migrator
```

### From Source

```bash
git clone https://github.com/aayush598/cocotb2-migrator.git
cd cocotb2-migrator
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Basic usage - migrate all Python files in a directory
cocotb2-migrator /path/to/your/cocotb/project

# Generate a migration report
cocotb2-migrator /path/to/project --report migration_report.json

# Example with real path
cocotb2-migrator ./testbenches --report ./reports/migration.json
```

### Python API

```python
from cocotb2_migrator.main import main
from cocotb2_migrator.migrator import migrate_directory
from cocotb2_migrator.report import MigrationReport

# Using the API directly
report = MigrationReport()
migrate_directory('/path/to/project', report)
report.print()  # Display in console
report.save('migration_report.json')  # Save to file

```

## Migration Transformations

### 1. Coroutine to Async/Await

Converts legacy coroutine syntax to modern async/await:

**Before:**
```python
@cocotb.coroutine
def my_test_function(dut):
    yield Timer(10)
    yield RisingEdge(dut.clk)
```

**After:**
```python
async def my_test_function(dut):
    await Timer(10)
    await RisingEdge(dut.clk)
```

### 2. Fork to Start Soon

Updates concurrent execution syntax:

**Before:**
```python
handle = cocotb.fork(my_background_task())
```

**After:**
```python
handle = cocotb.start_soon(my_background_task())
```

### 3. Handle Value Access

Modernizes signal value access patterns:

**Before:**
```python
val = dut.signal.value.get_value()
integer_val = dut.signal.value.integer
binary_str = dut.signal.value.binstr
raw_val = dut.signal.value.raw_value
```

**After:**
```python
val = dut.signal.value
integer_val = int(dut.signal.value)
binary_str = format(dut.signal.value, 'b')
raw_val = dut.signal.value
```

### 4. Binary Value Updates

Updates binary value imports and usage:

**Before:**
```python
from cocotb.binary import BinaryValue
val = cocotb.binary.BinaryValue(0)
val = BinaryValue(value=0, bigEndian=True)
```

**After:**
```python
from cocotb import BinaryValue
val = cocotb.BinaryValue(0)
val = BinaryValue(value=0, big_endian=True)
```

### 5. Deprecated Imports

Removes or updates deprecated import statements:

**Before:**
```python
from cocotb.decorators import coroutine
from cocotb.result import TestFailure
from cocotb.regression import TestFactory
```

**After:**
```python
from cocotb import coroutine
from cocotb import TestFailure
# cocotb.regression import removed (no longer needed)
```

## Architecture

### Core Components

#### 1. Parser (`parser.py`)
- **TransformerPipeline**: Orchestrates the application of multiple transformers
- **File Operations**: Handles reading, writing, and backup of source files
- **Syntax Highlighting**: Provides rich console output with code highlighting

#### 2. Transformers (`transformers/`)
All transformers inherit from `BaseCocotbTransformer` and implement specific migration patterns:

- **`CoroutineToAsyncTransformer`**: Handles `@cocotb.coroutine` → `async def`
- **`ForkTransformer`**: Converts `cocotb.fork()` → `cocotb.start_soon()`
- **`HandleTransformer`**: Updates signal value access patterns
- **`BinaryValueTransformer`**: Migrates binary value usage
- **`DeprecatedImportsTransformer`**: Cleans up deprecated imports

#### 3. Migration Engine (`migrator.py`)
- **File Discovery**: Recursively finds Python files in target directories
- **Transformation Application**: Applies all transformers to discovered files
- **Progress Tracking**: Monitors and reports transformation progress

#### 4. Reporting (`report.py`)
- **Console Output**: Rich table format with color-coded results
- **JSON Export**: Structured data for integration with other tools
- **Statistics**: Comprehensive migration statistics and summaries

### Technical Details

#### LibCST Integration
The tool uses LibCST (Concrete Syntax Tree) for parsing and transforming Python code, ensuring:
- **Preservation of Formatting**: Comments, whitespace, and code style are maintained
- **Accurate Transformations**: Syntactically correct transformations
- **Error Handling**: Robust parsing with detailed error reporting

#### Transformer Pipeline
```python
ALL_TRANSFORMERS = [
    CoroutineToAsyncTransformer,
    ForkTransformer,
    BinaryValueTransformer,
    HandleTransformer,
    DeprecatedImportsTransformer,
]
```

Transformers are applied in sequence, with each transformer:
1. Parsing the current AST state
2. Applying its specific transformations
3. Returning the modified AST
4. Tracking whether modifications were made

## Requirements

- **Python**: 3.8 or higher
- **Dependencies**:
  - `libcst >= 1.0.1`: For parsing and transforming Python code
  - `click`: Command-line interface framework
  - `termcolor`: Terminal color output
  - `rich`: Enhanced console output with syntax highlighting

## Development

### Project Structure

```
cocotb2_migrator/
├── __init__.py
├── main.py                 # Entry point and CLI coordination
├── cli.py                  # Command-line argument parsing
├── migrator.py             # Core migration logic
├── parser.py               # File parsing and transformation pipeline
├── report.py               # Migration reporting and statistics
└── transformers/
    ├── __init__.py
    ├── base.py             # Base transformer class
    ├── coroutine_transformer.py
    ├── fork_transformer.py
    ├── handle_transformer.py
    ├── binaryvalue_transformer.py
    └── deprecated_imports_transformer.py
```

### Adding New Transformers

1. Create a new transformer class inheriting from `BaseCocotbTransformer`:

```python
from cocotb2_migrator.transformers.base import BaseCocotbTransformer
import libcst as cst

class MyCustomTransformer(BaseCocotbTransformer):
    name = "MyCustomTransformer"
    
    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        # Your transformation logic here
        if self.should_transform(original_node):
            self.mark_modified()
            return self.transform_node(updated_node)
        return updated_node
```

2. Add the transformer to `ALL_TRANSFORMERS` in `migrator.py`:

```python
ALL_TRANSFORMERS = [
    CoroutineToAsyncTransformer,
    ForkTransformer,
    BinaryValueTransformer,
    HandleTransformer,
    DeprecatedImportsTransformer,
    MyCustomTransformer,  # Add your transformer here
]
```

### Testing

The project includes example files for testing transformations:

- `examples/legacy_tb.py`: Legacy cocotb 1.x testbench
- `examples/test_example.py`: Comprehensive test cases for all transformers

Run migrations on test files:

```bash
python -m cocotb2_migrator examples/ --report test_report.json
