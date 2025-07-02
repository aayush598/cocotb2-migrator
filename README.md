
# Cocotb v2 Code Migration Helper 🛠️

A tool to help users migrate their Cocotb testbenches from **v1.x** to **v2.x** style. Cocotb v2 introduces breaking changes such as replacing `@cocotb.coroutine` with `async def`, `yield` with `await`, and `cocotb.fork()` with `cocotb.start_soon()`.

This migration helper identifies and optionally rewrites deprecated Cocotb v1 constructs to their v2 equivalents using [LibCST](https://libcst.readthedocs.io/), a concrete syntax tree parser and code rewriter.

---

## 🔧 Features

- ✅ Detects v1-only features:
  - `@cocotb.coroutine`
  - `yield`-based coroutines
  - `ReturnValue(value)`
  - `cocotb.fork()`
- 🛠️ Migrates to v2-compatible constructs:
  - Replaces `yield` with `await`
  - Replaces `cocotb.fork()` with `cocotb.start_soon()`
  - Converts `ReturnValue(x)` to `return x`
- 💡 Outputs `.migrated.py` files next to originals (safe by default)
- 📝 Preserves comments and formatting with LibCST

---

## 📦 Requirements

- Python 3.8+
- [`libcst`](https://github.com/Instagram/LibCST)

Install dependencies:

```bash
pip install libcst
````

---

## 🚀 Usage

### 🔍 Check mode (dry-run)

Scans and reports deprecated Cocotb v1 constructs:

```bash
python cocotb_migrate.py --check path/to/your/testbenches/
```

---

### 🔁 Apply mode (safe rewrite)

Migrates v1-style testbenches and creates `*.migrated.py` files:

```bash
python cocotb_migrate.py --apply path/to/your/testbenches/
```

---

### ⚠️ In-place modification (advanced)

Modifies the original files directly (use with caution):

```bash
python cocotb_migrate.py --apply --inplace path/to/your/testbenches/
```

---

## 🧪 Example

### Input (`test_my_dut.py`)

```python
@cocotb.coroutine
def my_test(dut):
    yield Timer(10, units='ns')
    ReturnValue(42)
```

### Output (`test_my_dut.migrated.py`)

```python
async def my_test(dut):
    await Timer(10, units='ns')
    return 42
```

---

## 🧪 Testing

### Manual test

1. Copy your Cocotb v1 test files into `testbenches/`.
2. Run:

```bash
python cocotb_migrate.py --apply testbenches/
diff testbenches/test_my_dut.py testbenches/test_my_dut.migrated.py
```

3. Verify correctness with:

```bash
python -m py_compile testbenches/test_my_dut.migrated.py
```

---

### Automated unit test

Run included test cases:

```bash
python test_migrator.py
```

---

## 📁 Project Structure

```
cocotb_migrator/
├── cocotb_migrate.py        # Migration tool
├── testbenches/
│   └── test_my_dut.py       # Sample v1-style testbench
├── test_migrator.py         # Optional test script (unittest)
└── README.md
```

---

## 🧠 Future Enhancements

* Auto-format migrated code using `black` or `ruff`
* CI integration (GitHub Actions)
* Web-based UI for migration preview
* Batch diff viewer or HTML report generator

---

## 👤 Mentor

**Kaleb Barrett**

---

## 📚 References

* [Cocotb v2 Release Notes](https://docs.cocotb.org/en/latest/release_notes.html)
* [LibCST](https://libcst.readthedocs.io/)
* [Cocotb Documentation](https://docs.cocotb.org/en/stable/)
* [Blog: Tools for Rewriting Python Code](https://lukeplant.me.uk/blog/posts/tools-for-rewriting-python-code/)

---

## 🛡️ License

MIT License — free to use, modify, and distribute.

---

## ❤️ Contributions Welcome

Have an idea for improvement? Submit a pull request or open an issue!
