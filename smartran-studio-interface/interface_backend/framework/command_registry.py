"""
Command registry system for CLI framework

Provides decorator-based command registration with metadata,
automatic help generation, and command routing.
"""
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ArgumentType(Enum):
    """Argument types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    CHOICE = "choice"


@dataclass
class CommandArgument:
    """Definition of a command argument"""
    name: str
    arg_type: ArgumentType
    required: bool = False
    default: Any = None
    choices: Optional[List[str]] = None
    help_text: str = ""


@dataclass
class CommandMetadata:
    """Metadata about a command"""
    name: str
    description: str
    usage: str
    examples: List[str]
    arguments: List[CommandArgument]
    response_type: str  # ResponseType as string to avoid circular import
    category: str = "General"
    aliases: List[str] = field(default_factory=list)
    requires_connection: bool = True
    long_description: str = ""  # Detailed help text


class CommandRegistry:
    """Central registry for all CLI commands"""
    
    def __init__(self):
        self.commands: Dict[str, Dict] = {}
        self.categories: Dict[str, List[str]] = {}
    
    def register(self, metadata: CommandMetadata, handler: Callable):
        """Register a command with its handler"""
        self.commands[metadata.name] = {
            'handler': handler,
            'metadata': metadata
        }
        
        # Register aliases
        if metadata.aliases:
            for alias in metadata.aliases:
                self.commands[alias] = self.commands[metadata.name]
        
        # Add to category
        if metadata.category not in self.categories:
            self.categories[metadata.category] = []
        if metadata.name not in self.categories[metadata.category]:
            self.categories[metadata.category].append(metadata.name)
    
    def get_command(self, name: str) -> Optional[Dict]:
        """Get command by name or alias"""
        return self.commands.get(name)
    
    def list_commands(self, category: Optional[str] = None) -> List[str]:
        """List all commands, optionally filtered by category"""
        if category:
            return self.categories.get(category, [])
        return list(self.commands.keys())
    
    def generate_help(self, command_name: Optional[str] = None) -> str:
        """Auto-generate help text from metadata"""
        if command_name:
            cmd = self.get_command(command_name)
            if not cmd:
                return f"Unknown command: {command_name}"
            return self._generate_command_help(cmd['metadata'])
        else:
            return self._generate_global_help()
    
    def _generate_command_help(self, metadata: CommandMetadata) -> str:
        """Generate help for a specific command"""
        help_text = f"{metadata.description}\n\n"
        help_text += f"Usage: {metadata.usage}\n\n"
        
        if metadata.arguments:
            help_text += "Arguments:\n"
            for arg in metadata.arguments:
                req = "(required)" if arg.required else "(optional)"
                help_text += f"  --{arg.name}  {arg.help_text} {req}\n"
            help_text += "\n"
        
        if metadata.examples:
            help_text += "Examples:\n"
            for example in metadata.examples:
                help_text += f"  {example}\n"
        
        return help_text
    
    def _generate_global_help(self) -> str:
        """Generate global help listing all commands by category"""
        help_text = "CNS CLI - Available Commands\n\n"
        
        for category, commands in sorted(self.categories.items()):
            help_text += f"{category.upper()}:\n"
            for cmd_name in commands:
                cmd = self.commands[cmd_name]
                metadata = cmd['metadata']
                help_text += f"  {cmd_name:<20} {metadata.description}\n"
            help_text += "\n"
        
        help_text += "Use 'cns <command> --help' for detailed command help\n"
        return help_text


# Global registry instance
registry = CommandRegistry()


def command(
    name: str,
    description: str,
    usage: str = None,
    long_description: str = None,
    examples: List[str] = None,
    arguments: List[CommandArgument] = None,
    response_type: str = "text",
    category: str = "General",
    aliases: List[str] = None,
    requires_connection: bool = True
):
    """Decorator to register a command"""
    def decorator(func: Callable):
        metadata = CommandMetadata(
            name=name,
            description=description,
            usage=usage or f"cns {name}",
            examples=examples or [],
            arguments=arguments or [],
            response_type=response_type,
            category=category,
            aliases=aliases or [],
            requires_connection=requires_connection,
            long_description=long_description or description
        )
        
        registry.register(metadata, func)
        # Store metadata on function for easy access
        func.metadata = {'long_description': metadata.long_description}
        return func
    
    return decorator

