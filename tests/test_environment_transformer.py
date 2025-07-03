import libcst as cst
from cocotb2_migrator.transformers.environment_transformer import EnvironmentTransformer


def transform_code(source: str) -> str:
    # Wrap code in a valid module and apply transformer
    tree = cst.parse_module(source)
    transformer = EnvironmentTransformer()
    modified_tree = tree.visit(transformer)
    return modified_tree.code


# def test_environ_subscript_transformation():
#     assert transform_code('os.environ["MODULE"]') == 'os.environ["COCOTB_TEST_MODULES"]'
#     assert transform_code('os.environ["TOPLEVEL"]') == 'os.environ["COCOTB_TOPLEVEL"]'
#     assert transform_code('os.environ["RANDOM_SEED"]') == 'os.environ["COCOTB_RANDOM_SEED"]'


def test_environ_get_transformation():
    assert transform_code('os.environ.get("COVERAGE")') == 'os.environ.get("COCOTB_USER_COVERAGE")'
    assert transform_code('os.environ.get("TESTCASE", "default")') == 'os.environ.get("COCOTB_TESTCASE", "default")'


def test_getenv_transformation():
    assert transform_code('os.getenv("PLUSARGS")') == 'os.getenv("COCOTB_PLUSARGS")'
    assert transform_code('os.getenv("COVERAGE_RCFILE", "rc.ini")') == 'os.getenv("COCOTB_COVERAGE_RCFILE", "rc.ini")'


def test_attribute_language_transformation():
    assert transform_code('cocotb.LANGUAGE') == 'os.environ["TOPLEVEL_LANG"]'


def test_attribute_argc_transformation():
    assert transform_code('cocotb.argc') == 'len(cocotb.argv)'


def test_unmapped_env_var_unchanged():
    src = 'os.environ["UNKNOWN"]'
    assert transform_code(src) == 'os.environ["UNKNOWN"]'

    src_get = 'os.environ.get("UNKNOWN")'
    assert transform_code(src_get) == 'os.environ.get("UNKNOWN")'

    src_getenv = 'os.getenv("UNKNOWN")'
    assert transform_code(src_getenv) == 'os.getenv("UNKNOWN")'


def test_unrelated_code_unchanged():
    src = 'print("hello world")'
    assert transform_code(src) == 'print("hello world")'
