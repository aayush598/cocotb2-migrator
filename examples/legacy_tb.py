import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue

@cocotb.coroutine
def legacy_wait():
    yield Timer(10)

@cocotb.test()
def test_something(dut):
    yield Timer(5)
    val = BinaryValue("1010")
