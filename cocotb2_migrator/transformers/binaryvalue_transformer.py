import libcst as cst
from libcst import Attribute, Name, Arg, Call
from typing import Union, Sequence
from cocotb2_migrator.transformers.base import BaseCocotbTransformer


class BinaryValueTransformer(BaseCocotbTransformer):
    """
    Transforms BinaryValue usage to LogicArray according to cocotb 2.0 migration guide.
    
    Key transformations:
    1. BinaryValue(...) -> LogicArray(...)
    2. BinaryValue(int_val, n_bits) -> LogicArray.from_unsigned(int_val, n_bits)
    3. BinaryValue(int_val, n_bits, SIGNED) -> LogicArray.from_signed(int_val, n_bits)
    4. BinaryValue(bytes_val, bigEndian=True) -> LogicArray.from_bytes(bytes_val, byteorder="big")
    5. Property access transformations (integer -> to_unsigned(), etc.)
    """
    name = "BinaryValueTransformer"
    
    def __init__(self):
        super().__init__()
        self.signed_magnitude_found = False
        self.warning_comments = []

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        """Handle imports like 'from cocotb.binary import BinaryValue'"""
        if (original_node.module and 
            isinstance(original_node.module, cst.Attribute) and
            isinstance(original_node.module.value, cst.Name) and
            original_node.module.value.value == "cocotb" and
            original_node.module.attr.value == "binary"):
            
            # Check if BinaryValue is being imported
            if original_node.names and isinstance(original_node.names, cst.ImportStar):
                # from cocotb.binary import * - add warning comment
                self.mark_modified()
                return updated_node.with_changes(
                    leading_lines=[
                        cst.SimpleStatementLine([
                            cst.Expr(cst.SimpleString('"""WARNING: BinaryValue was removed, update imports manually"""'))
                        ])
                    ]
                )
            elif original_node.names and isinstance(original_node.names, Sequence):
                new_names = []
                needs_types_import = False
                
                for name_item in original_node.names:
                    if isinstance(name_item, cst.ImportAlias):
                        if name_item.name.value == "BinaryValue":
                            # Replace BinaryValue import with LogicArray from cocotb.types
                            needs_types_import = True
                            self.mark_modified()
                        elif name_item.name.value == "BinaryRepresentation":
                            # BinaryRepresentation is no longer needed
                            self.mark_modified()
                            continue
                        else:
                            new_names.append(name_item)
                    else:
                        new_names.append(name_item)
                
                if needs_types_import:
                    # Return new import for LogicArray from cocotb.types
                    return cst.ImportFrom(
                        module=cst.Attribute(value=cst.Name("cocotb"), attr=cst.Name("types")),
                        names=[cst.ImportAlias(name=cst.Name("LogicArray"))]
                    )
                elif new_names:
                    return updated_node.with_changes(names=new_names)
                else:
                    # Remove the import entirely
                    return cst.RemovalSentinel.REMOVE
        
        return updated_node

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        """Handle BinaryValue constructor calls and module path transformations"""
        
        func_name = self._get_full_func_name(original_node.func)
        
        if func_name in {"BinaryValue", "cocotb.binary.BinaryValue", "cocotb.BinaryValue"}:
            self.mark_modified()
            return self._transform_binary_value_call(original_node, updated_node)
        
        return updated_node

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        """Handle attribute access transformations"""
        
        # Handle cocotb.binary.BinaryValue -> cocotb.types.LogicArray
        if (isinstance(original_node.value, cst.Attribute) and
            isinstance(original_node.value.value, cst.Name) and
            original_node.value.value.value == "cocotb" and
            original_node.value.attr.value == "binary" and
            original_node.attr.value == "BinaryValue"):
            self.mark_modified()
            return cst.Attribute(
                value=cst.Attribute(value=cst.Name("cocotb"), attr=cst.Name("types")),
                attr=cst.Name("LogicArray")
            )
        
        # Handle cocotb.BinaryValue -> cocotb.types.LogicArray
        if (isinstance(original_node.value, cst.Name) and
            original_node.value.value == "cocotb" and
            original_node.attr.value == "BinaryValue"):
            self.mark_modified()
            return cst.Attribute(
                value=cst.Attribute(value=cst.Name("cocotb"), attr=cst.Name("types")),
                attr=cst.Name("LogicArray")
            )
        
        # Handle property access transformations
        if isinstance(original_node.value, cst.Name):
            var_name = original_node.value.value
            attr_name = original_node.attr.value
            
            # Transform property access: obj.integer -> obj.to_unsigned()
            if attr_name == "integer":
                self.mark_modified()
                return cst.Call(
                    func=cst.Attribute(value=cst.Name(var_name), attr=cst.Name("to_unsigned")),
                    args=[]
                )
            
            # Transform property access: obj.signed_integer -> obj.to_signed()
            elif attr_name == "signed_integer":
                self.mark_modified()
                return cst.Call(
                    func=cst.Attribute(value=cst.Name(var_name), attr=cst.Name("to_signed")),
                    args=[]
                )
            
            # Transform property access: obj.binstr -> str(obj)
            elif attr_name == "binstr":
                self.mark_modified()
                return cst.Call(
                    func=cst.Name("str"),
                    args=[cst.Arg(value=cst.Name(var_name))]
                )
            
            # Transform property access: obj.buff -> obj.to_bytes(byteorder="big")
            elif attr_name == "buff":
                self.mark_modified()
                return cst.Call(
                    func=cst.Attribute(value=cst.Name(var_name), attr=cst.Name("to_bytes")),
                    args=[cst.Arg(keyword=cst.Name("byteorder"), value=cst.SimpleString('"big"'), equal=cst.AssignEqual(whitespace_before=cst.SimpleWhitespace(""), whitespace_after=cst.SimpleWhitespace("")))]
                )
        
        return updated_node

    def _transform_binary_value_call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Transform BinaryValue constructor to appropriate LogicArray method"""
        
        args = list(original_node.args)
        
        # Parse arguments
        value_arg = None
        n_bits_arg = None
        binary_repr_arg = None
        big_endian_arg = None
        
        # Process positional arguments
        pos_args = [arg for arg in args if arg.keyword is None]
        if len(pos_args) >= 1:
            value_arg = pos_args[0]
        if len(pos_args) >= 2:
            n_bits_arg = pos_args[1]
        
        # Process keyword arguments (be careful not to double-process n_bits)
        for arg in args:
            if arg.keyword:
                if arg.keyword.value == "n_bits" and n_bits_arg is None:
                    # Only use keyword n_bits if we don't have a positional one
                    n_bits_arg = arg
                elif arg.keyword.value == "binaryRepresentation":
                    binary_repr_arg = arg
                elif arg.keyword.value in ["bigEndian", "big_endian"]:
                    big_endian_arg = arg
        
        # Determine function name based on the original call's module path
        func_name = self._get_full_func_name(original_node.func)
        if func_name == "cocotb.binary.BinaryValue":
            # Use fully qualified path for cocotb.binary.BinaryValue
            logic_array_func = cst.Attribute(
                value=cst.Attribute(value=cst.Name("cocotb"), attr=cst.Name("types")),
                attr=cst.Name("LogicArray")
            )
        else:
            # Use bare LogicArray for cocotb.BinaryValue and imported BinaryValue
            logic_array_func = cst.Name("LogicArray")
        
        # Special case: string with bigEndian should be treated as bytes
        if (self._is_string_value(value_arg) and big_endian_arg):
            # Treat as bytes case
            new_func = cst.Attribute(
                value=logic_array_func,
                attr=cst.Name("from_bytes")
            )
            
            byteorder = "big" if self._is_big_endian(big_endian_arg) else "little"
            new_args = [
                cst.Arg(value=value_arg.value),
                cst.Arg(
                    keyword=cst.Name("byteorder"), 
                    value=cst.SimpleString(f'"{byteorder}"'),
                    equal=cst.AssignEqual(whitespace_before=cst.SimpleWhitespace(""), whitespace_after=cst.SimpleWhitespace(""))
                )
            ]
            
            return cst.Call(func=new_func, args=new_args)
        
        # Determine the appropriate LogicArray constructor
        if binary_repr_arg:
            # Check if it's SIGNED representation
            if self._is_signed_representation(binary_repr_arg.value):
                # LogicArray.from_signed(value, n_bits)
                new_func = cst.Attribute(
                    value=logic_array_func,
                    attr=cst.Name("from_signed")
                )
                new_args = []
                if value_arg:
                    new_args.append(cst.Arg(value=value_arg.value))
                if n_bits_arg:
                    new_args.append(cst.Arg(value=n_bits_arg.value))
                
                return cst.Call(func=new_func, args=new_args)
            elif self._is_signed_magnitude_representation(binary_repr_arg.value):
                # SIGNED_MAGNITUDE has no equivalent - mark for warning and create fallback
                self.signed_magnitude_found = True
                new_args = []
                if value_arg:
                    new_args.append(cst.Arg(value=value_arg.value))
                else:
                    new_args.append(cst.Arg(value=cst.SimpleString('"0"')))
                
                # Create LogicArray call
                return cst.Call(func=logic_array_func, args=new_args)
            else:
                # Other binary representations - default handling
                return cst.Call(
                    func=logic_array_func,
                    args=[cst.Arg(value=cst.SimpleString('"0"'))]
                )
        
        elif self._is_bytes_value(value_arg):
            # LogicArray.from_bytes(bytes_val, byteorder="big"|"little")
            new_func = cst.Attribute(
                value=logic_array_func,
                attr=cst.Name("from_bytes")
            )
            
            byteorder = "big" if self._is_big_endian(big_endian_arg) else "little"
            new_args = [
                cst.Arg(value=value_arg.value),
                cst.Arg(
                    keyword=cst.Name("byteorder"), 
                    value=cst.SimpleString(f'"{byteorder}"'),
                    equal=cst.AssignEqual(whitespace_before=cst.SimpleWhitespace(""), whitespace_after=cst.SimpleWhitespace(""))
                )
            ]
            
            return cst.Call(func=new_func, args=new_args)
        
        elif self._is_integer_value(value_arg) and n_bits_arg:
            # LogicArray.from_unsigned(int_val, n_bits)
            new_func = cst.Attribute(
                value=logic_array_func,
                attr=cst.Name("from_unsigned")
            )
            
            new_args = [
                cst.Arg(value=value_arg.value),
                cst.Arg(value=n_bits_arg.value)
            ]
            
            return cst.Call(func=new_func, args=new_args)
            
        else:
            # Default case: LogicArray(value)
            new_args = []
            if value_arg:
                new_args.append(cst.Arg(value=value_arg.value))
            
            return cst.Call(func=logic_array_func, args=new_args)

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Add warning comment at the top of the module if SIGNED_MAGNITUDE was found"""
        if self.signed_magnitude_found:
            # Create warning comment as a comment line
            warning_comment = cst.SimpleStatementLine(
                body=[cst.Pass()],
                leading_lines=[
                    cst.EmptyLine(
                        comment=cst.Comment("# WARNING: BinaryRepresentation.SIGNED_MAGNITUDE has no LogicArray equivalent")
                    )
                ]
            )
            
            # Add warning to the beginning of the module
            new_body = [warning_comment] + list(updated_node.body)
            return updated_node.with_changes(body=new_body)
        
        return updated_node

    def _get_full_func_name(self, func_node: cst.BaseExpression) -> str:
        """Helper to reconstruct the full dotted name from an Attribute/Name chain"""
        if isinstance(func_node, cst.Name):
            return func_node.value
        elif isinstance(func_node, cst.Attribute):
            parts = []
            current = func_node
            while isinstance(current, cst.Attribute):
                parts.insert(0, current.attr.value)
                current = current.value
            if isinstance(current, cst.Name):
                parts.insert(0, current.value)
            return ".".join(parts)
        return ""

    def _is_signed_representation(self, node: cst.BaseExpression) -> bool:
        """Check if the node represents SIGNED binary representation"""
        if isinstance(node, cst.Attribute):
            return (isinstance(node.value, cst.Name) and 
                   node.value.value == "BinaryRepresentation" and
                   node.attr.value in ["SIGNED", "TWOS_COMPLEMENT"])
        return False

    def _is_signed_magnitude_representation(self, node: cst.BaseExpression) -> bool:
        """Check if the node represents SIGNED_MAGNITUDE binary representation"""
        if isinstance(node, cst.Attribute):
            return (isinstance(node.value, cst.Name) and 
                   node.value.value == "BinaryRepresentation" and
                   node.attr.value == "SIGNED_MAGNITUDE")
        return False

    def _is_bytes_value(self, arg: cst.Arg) -> bool:
        """Check if the argument is a bytes literal"""
        if arg and isinstance(arg.value, (cst.SimpleString, cst.ConcatenatedString)):
            # Check for b"..." or b'...' prefix
            if isinstance(arg.value, cst.SimpleString):
                return arg.value.value.startswith(('b"', "b'"))
        return False

    def _is_string_value(self, arg: cst.Arg) -> bool:
        """Check if the argument is a string literal (not bytes)"""
        if arg and isinstance(arg.value, (cst.SimpleString, cst.ConcatenatedString)):
            if isinstance(arg.value, cst.SimpleString):
                return arg.value.value.startswith(('"', "'")) and not arg.value.value.startswith(('b"', "b'"))
        return False

    def _is_integer_value(self, arg: cst.Arg) -> bool:
        """Check if the argument is likely an integer"""
        if arg and isinstance(arg.value, (cst.Integer, cst.UnaryOperation)):
            return True
        return False

    def _is_big_endian(self, big_endian_arg: cst.Arg) -> bool:
        """Determine endianness from bigEndian argument"""
        if big_endian_arg and isinstance(big_endian_arg.value, cst.Name):
            return big_endian_arg.value.value == "True"
        return True  # Default to big endian

    def has_signed_magnitude_warning(self) -> bool:
        """Check if SIGNED_MAGNITUDE was encountered during transformation"""
        return self.signed_magnitude_found