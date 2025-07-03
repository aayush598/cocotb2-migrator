# ========================
# Deprecated Imports
# ========================

from cocotb import coroutine       # Expected: from cocotb import coroutine
from cocotb import TestFailure         # Expected: from cocotb import TestFailure

# ========================
# Fork Transformation
# ========================

# Old: cocotb.fork(my_task())
# Expected: cocotb.start_soon(my_task())
cocotb.start_soon(my_task())

# ========================
# Handle Transformations
# ========================

# Old: val = sig.value.get_value()
# Expected: val = sig.value
val = sig.value

# Old: i = sig.value.integer
# Expected: i = int(sig.value)
i = int(sig.value)

# Old: b = sig.value.binstr
# Expected: b = format(sig.value, 'b')
b = format(sig.value, 'b')

# Old: r = sig.value.raw_value
# Expected: r = sig.value
r = sig.value

# ========================
# BinaryValue Transformation
# ========================

# Old: x = cocotb.binary.BinaryValue(0)
# Expected: x = cocotb.BinaryValue(0)
x = cocotb.BinaryValue(0)

# Old: x = cocotb.BinaryValue(value=0, bigEndian=True)
# Expected: x = cocotb.BinaryValue(value=0, big_endian=True)
x = cocotb.BinaryValue(value=0, big_endian=True)
