"""
Simple instance-based argument parser for commands

This parser is used by commands that parse their own arguments
instead of using CommandArgument definitions.
"""
from typing import Any, Dict, List, Optional, Tuple, Type


class ParsedArgs(dict):
    """Dictionary-like object for parsed arguments, allowing attribute access"""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None  # Return None for missing attributes instead of raising

    def __setattr__(self, name, value):
        self[name] = value


class SimpleArgumentParser:
    """Instance-based argument parser with type conversion"""
    
    def __init__(self, valid_flags: Optional[Dict[str, Type]] = None):
        """
        Initialize parser with valid flag definitions
        
        Args:
            valid_flags: Dict mapping flag names to Python types (str, int, float, bool)
        """
        self.valid_flags = valid_flags if valid_flags is not None else {}

    def parse_arguments(self, args: List[str]) -> Tuple[ParsedArgs, List[str]]:
        """
        Parse arguments into flags and positional args
        
        Args:
            args: List of argument strings
            
        Returns:
            Tuple of (parsed_args, positional_args)
        """
        parsed_args = ParsedArgs()
        positional_args = []
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            if arg.startswith("--"):
                key, value, consumed = self._parse_flag(arg, args, i)
                if key:
                    parsed_args[key] = value
                    i += consumed
                else:
                    positional_args.append(arg)
                    i += 1
            else:
                positional_args.append(arg)
                i += 1
        
        # Add help flag if not present
        if 'help' not in parsed_args:
            parsed_args['help'] = False
            
        return parsed_args, positional_args

    def _parse_flag(self, arg: str, all_args: List[str], index: int) -> Tuple[Optional[str], Any, int]:
        """
        Parse a flag argument
        
        Returns:
            Tuple of (key, value, num_args_consumed)
        """
        key = None
        value = None
        consumed = 1
        
        # Handle --flag=value format
        if "=" in arg:
            key, val_str = arg[2:].split("=", 1)
            value = self._convert_value(key, val_str)
        # Handle --flag value format
        elif index + 1 < len(all_args) and not all_args[index + 1].startswith("--"):
            key = arg[2:]
            val_str = all_args[index + 1]
            value = self._convert_value(key, val_str)
            consumed = 2
        else:
            # Flag without value (boolean)
            key = arg[2:]
            value = True
        
        if key:
            # Normalize key (replace hyphens with underscores)
            key = key.replace("-", "_")
            return key, value, consumed
            
        return None, None, consumed

    def _convert_value(self, key: str, value_str: str) -> Any:
        """Convert value string to appropriate type"""
        # Normalize key
        key = key.replace("-", "_")
        
        # Get target type
        target_type = self.valid_flags.get(key, str)
        
        try:
            if target_type == bool:
                return value_str.lower() in ('true', '1', 't', 'y', 'yes')
            elif target_type == int:
                return int(value_str)
            elif target_type == float:
                return float(value_str)
            else:
                return value_str
        except (ValueError, AttributeError):
            # If conversion fails, return as string
            return value_str

