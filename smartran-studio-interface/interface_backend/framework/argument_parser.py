"""
Argument parser for CLI framework

Parses and validates command arguments against definitions
from command metadata.
"""
from typing import List, Dict, Any
from framework.command_registry import CommandArgument, ArgumentType
from framework.response_types import CommandError


class ArgumentParser:
    """Parse and validate command arguments"""
    
    @staticmethod
    def parse(args: List[str], argument_defs: List[CommandArgument]) -> Dict[str, Any]:
        """
        Parse command arguments against definitions
        
        Args:
            args: Raw argument strings from user
            argument_defs: Argument definitions from command metadata
            
        Returns:
            Dictionary of parsed and validated arguments
            
        Raises:
            CommandError: If parsing or validation fails
        """
        parsed = {}
        arg_dict = {}
        
        # Parse --flag=value or --flag value format
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg.startswith("--"):
                if "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    arg_dict[key.replace("-", "_")] = value
                    i += 1
                elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                    key = arg[2:].replace("-", "_")
                    arg_dict[key] = args[i + 1]
                    i += 2
                else:
                    # Flag without value (boolean)
                    key = arg[2:].replace("-", "_")
                    arg_dict[key] = True
                    i += 1
            else:
                raise CommandError(
                    f"Invalid argument format: {arg}",
                    suggestions=["Arguments must start with --", "Example: --flag=value or --flag value"]
                )
        
        # Validate against definitions
        defined_args = {arg.name: arg for arg in argument_defs}
        
        for arg_name, arg_value in arg_dict.items():
            if arg_name not in defined_args:
                raise CommandError(
                    f"Unknown argument: --{arg_name}",
                    suggestions=[f"Valid arguments: {', '.join(defined_args.keys())}"]
                )
            
            arg_def = defined_args[arg_name]
            parsed[arg_name] = ArgumentParser._validate_and_convert(
                arg_name, arg_value, arg_def
            )
        
        # Check required arguments
        for arg_def in argument_defs:
            if arg_def.required and arg_def.name not in parsed:
                raise CommandError(
                    f"Missing required argument: --{arg_def.name}",
                    suggestions=[f"Usage: --{arg_def.name}=<value>"]
                )
            elif arg_def.name not in parsed and arg_def.default is not None:
                parsed[arg_def.name] = arg_def.default
        
        return parsed
    
    @staticmethod
    def _validate_and_convert(name: str, value: Any, arg_def: CommandArgument) -> Any:
        """Validate and convert argument value to correct type"""
        try:
            if arg_def.arg_type == ArgumentType.INTEGER:
                return int(value)
            
            elif arg_def.arg_type == ArgumentType.FLOAT:
                return float(value)
            
            elif arg_def.arg_type == ArgumentType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                if value.lower() in ['true', '1', 'yes', 'y']:
                    return True
                elif value.lower() in ['false', '0', 'no', 'n']:
                    return False
                else:
                    raise ValueError()
            
            elif arg_def.arg_type == ArgumentType.CHOICE:
                if value not in arg_def.choices:
                    raise CommandError(
                        f"Invalid choice for --{name}: {value}",
                        suggestions=[f"Valid choices: {', '.join(arg_def.choices)}"]
                    )
                return value
            
            else:  # STRING
                return str(value)
        
        except (ValueError, TypeError):
            raise CommandError(
                f"Invalid value for --{name}: {value}",
                suggestions=[f"Expected type: {arg_def.arg_type.value}"]
            )

