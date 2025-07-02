import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.result import ReturnValue

@cocotb.coroutine
def reset_dut(dut):
    dut.reset <= 1
    yield Timer(100, units='ns')
    dut.reset <= 0
    yield RisingEdge(dut.clk)

@cocotb.test()
def test_basic_functionality(dut):
    yield reset_dut(dut)
    dut.input <= 0xA
    yield Timer(10, units='ns')
    yield RisingEdge(dut.clk)
    assert dut.output == 0xA, f"Expected output 0xA, got {dut.output.value}"

@cocotb.test()
def test_parallel_tasks(dut):
    yield reset_dut(dut)

    @cocotb.coroutine
    def stimulus():
        for i in range(4):
            dut.input <= i
            yield RisingEdge(dut.clk)

    @cocotb.coroutine
    def monitor():
        for _ in range(4):
            yield RisingEdge(dut.clk)
            print(f"Monitor saw output: {dut.output.value}")

    stim = cocotb.fork(stimulus())
    mon = cocotb.fork(monitor())
    yield stim.join()
    yield mon.join()

@cocotb.coroutine
def return_value_example(dut):
    yield Timer(1, units='ns')
    ReturnValue(42)
