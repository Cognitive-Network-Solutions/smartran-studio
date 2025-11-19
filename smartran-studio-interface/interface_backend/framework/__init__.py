"""
CNS CLI Framework - Reusable command framework for CLI applications
"""
from framework.response_types import (
    ResponseType,
    CommandResponse,
    CommandError,
    TableData,
    ChartData,
    InteractivePrompt
)
from framework.command_registry import (
    CommandRegistry,
    CommandMetadata,
    CommandArgument,
    ArgumentType,
    command,
    registry
)
# ArgumentParser from argument_parser.py (for query commands with CommandArgument)
from framework.argument_parser import ArgumentParser as FrameworkArgumentParser
# SimpleArgumentParser (for new commands with valid_flags)
from framework.simple_argument_parser import SimpleArgumentParser as ArgumentParser

__all__ = [
    # Response types
    'ResponseType',
    'CommandResponse',
    'CommandError',
    'TableData',
    'ChartData',
    'InteractivePrompt',
    # Command registry
    'CommandRegistry',
    'CommandMetadata',
    'CommandArgument',
    'ArgumentType',
    'command',
    'registry',
    # Argument parsers
    'ArgumentParser',
    'FrameworkArgumentParser',
]

