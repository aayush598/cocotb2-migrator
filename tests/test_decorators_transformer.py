import libcst as cst

from cocotb2_migrator.transformers.decorators_transformer import DecoratorsTransformer


def apply(src: str) -> str:
    return cst.parse_module(src).visit(DecoratorsTransformer()).code.strip()


# ---------------------------------------------------------------------------
# cocotb.decorators qualified usages
# ---------------------------------------------------------------------------


def test_coroutine_usage_rewritten():
    src = "cocotb.decorators.coroutine(fn)"
    expected = "cocotb.coroutine(fn)"
    assert apply(src) == expected


def test_test_usage_rewritten():
    src = "@cocotb.decorators.test\ndef t():\n    pass"
    expected = "@cocotb.test\ndef t():\n    pass"
    assert apply(src) == expected


def test_external_usage_rewritten():
    src = "cocotb.decorators.external(fn)"
    expected = "cocotb.task.bridge(fn)"
    assert apply(src) == expected


def test_function_usage_rewritten():
    src = "cocotb.decorators.function(fn)"
    expected = "cocotb.task.resume(fn)"
    assert apply(src) == expected


def test_public_usage_warns_and_stays():
    result = apply("cocotb.decorators.public(fn)")
    assert "# WARNING: `cocotb.decorators.public` was removed in cocotb 2.0" in result
    assert "cocotb.decorators.public(fn)" in result


def test_unrelated_attribute_untouched():
    src = "foo.decorators.bar()"
    assert apply(src) == "foo.decorators.bar()"


def test_unrelated_cocotb_attribute_untouched():
    src = "cocotb.trigger.rising_edge()"
    assert apply(src) == "cocotb.trigger.rising_edge()"
