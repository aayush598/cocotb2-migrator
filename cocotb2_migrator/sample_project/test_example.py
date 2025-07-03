import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue

@cocotb.coroutine
def test_basic(dut):
    yield Timer(10, units='ns')
    val = BinaryValue("1101")
    dut.signal <= val
