import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.result import ReturnValue

async def reset_dut(dut):
    dut.reset <= 1
    await Timer(100, units='ns')
    dut.reset <= 0
    await RisingEdge(dut.clk)

@cocotb.test()
def test_basic_functionality(dut):
    await reset_dut(dut)
    dut.input <= 0xA
    await Timer(10, units='ns')
    await RisingEdge(dut.clk)
    assert dut.output == 0xA, f"Expected output 0xA, got {dut.output.value}"

@cocotb.test()
def test_parallel_tasks(dut):
    await reset_dut(dut)

    async def stimulus():
        for i in range(4):
            dut.input <= i
            await RisingEdge(dut.clk)

    async def monitor():
        for _ in range(4):
            await RisingEdge(dut.clk)
            print(f"Monitor saw output: {dut.output.value}")

    stim = cocotb.fork(stimulus())
    mon = cocotb.fork(monitor())
    await stim.join()
    await mon.join()

async def return_value_example(dut):
    await Timer(1, units='ns')
    ReturnValue(42)
