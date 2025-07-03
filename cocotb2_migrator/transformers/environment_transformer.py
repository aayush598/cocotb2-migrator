# cocotb2_migrator/transformers/environment_transformer.py

import libcst as cst
from libcst import Subscript, Attribute, Name, SimpleString
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class EnvironmentTransformer(BaseCocotbTransformer):
    name = "EnvironmentTransformer"

    # Environment variable mappings
    ENV_VAR_MAPPINGS = {
        "MODULE": "COCOTB_TEST_MODULES",
        "TOPLEVEL": "COCOTB_TOPLEVEL", 
        "TESTCASE": "COCOTB_TESTCASE",
        "COVERAGE": "COCOTB_USER_COVERAGE",
        "COVERAGE_RCFILE": "COCOTB_COVERAGE_RCFILE",
        "PLUSARGS": "COCOTB_PLUSARGS",
        "RANDOM_SEED": "COCOTB_RANDOM_SEED",
    }

    def leave_Subscript(self, original_node: cst.Subscript, updated_node: cst.Subscript) -> cst.BaseExpression:
        """
        Transform environment variable access:
        os.environ["MODULE"] -> os.environ["COCOTB_TEST_MODULES"]
        """
        if isinstance(original_node.value, cst.Attribute):
            # Check for os.environ["VAR"]
            if (isinstance(original_node.value.value, cst.Name) and 
                original_node.value.value.value == "os" and
                original_node.value.attr.value == "environ"):
                
                if isinstance(original_node.slice, cst.Index):
                    if isinstance(original_node.slice.value, cst.SimpleString):
                        env_var = original_node.slice.value.value.strip('"\'')
                        if env_var in self.ENV_VAR_MAPPINGS:
                            new_var = self.ENV_VAR_MAPPINGS[env_var]
                            self.mark_modified()
                            return updated_node.with_changes(
                                slice=cst.Index(value=cst.SimpleString(f'"{new_var}"'))
                            )

        return updated_node

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        """
        Transform environment variable method calls:
        os.environ.get("MODULE") -> os.environ.get("COCOTB_TEST_MODULES")
        os.getenv("MODULE") -> os.getenv("COCOTB_TEST_MODULES")
        """
        # Handle os.environ.get("VAR")
        if isinstance(original_node.func, cst.Attribute):
            if (isinstance(original_node.func.value, cst.Attribute) and
                isinstance(original_node.func.value.value, cst.Name) and
                original_node.func.value.value.value == "os" and
                original_node.func.value.attr.value == "environ" and
                original_node.func.attr.value == "get"):
                
                if len(original_node.args) > 0:
                    first_arg = original_node.args[0]
                    if isinstance(first_arg.value, cst.SimpleString):
                        env_var = first_arg.value.value.strip('"\'')
                        if env_var in self.ENV_VAR_MAPPINGS:
                            new_var = self.ENV_VAR_MAPPINGS[env_var]
                            self.mark_modified()
                            new_args = [
                                cst.Arg(value=cst.SimpleString(f'"{new_var}"'))
                            ] + list(original_node.args[1:])
                            return updated_node.with_changes(args=new_args)

            # Handle os.getenv("VAR")
            elif (isinstance(original_node.func.value, cst.Name) and
                  original_node.func.value.value == "os" and
                  original_node.func.attr.value == "getenv"):
                
                if len(original_node.args) > 0:
                    first_arg = original_node.args[0]
                    if isinstance(first_arg.value, cst.SimpleString):
                        env_var = first_arg.value.value.strip('"\'')
                        if env_var in self.ENV_VAR_MAPPINGS:
                            new_var = self.ENV_VAR_MAPPINGS[env_var]
                            self.mark_modified()
                            new_args = [
                                cst.Arg(value=cst.SimpleString(f'"{new_var}"'))
                            ] + list(original_node.args[1:])
                            return updated_node.with_changes(args=new_args)

        return updated_node

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        """
        Transform deprecated cocotb attributes:
        - cocotb.LANGUAGE -> os.environ["TOPLEVEL_LANG"]
        - cocotb.argc -> len(cocotb.argv)
        """
        if isinstance(original_node.value, cst.Name) and original_node.value.value == "cocotb":
            attr_name = original_node.attr.value
            
            if attr_name == "LANGUAGE":
                self.mark_modified()
                return cst.Subscript(
                    value=cst.Attribute(
                        value=cst.Name("os"),
                        attr=cst.Name("environ")
                    ),
                    slice=[
                        cst.SubscriptElement(
                            slice=cst.Index(value=cst.SimpleString('"TOPLEVEL_LANG"'))
                        )
                    ]

                )
            
            elif attr_name == "argc":
                self.mark_modified()
                return cst.Call(
                    func=cst.Name("len"),
                    args=[cst.Arg(value=cst.Attribute(
                        value=cst.Name("cocotb"),
                        attr=cst.Name("argv")
                    ))]
                )

        return updated_node