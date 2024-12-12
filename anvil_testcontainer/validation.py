"""
Security and validation utilities for Anvil container operations.
These functions ensure safe handling of inputs and commands.
"""

import re
from typing import Any, Dict, List, Union


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


def validate_ethereum_address(address: str) -> bool:
    """
    Validate Ethereum address format.

    The function checks if the input matches the standard Ethereum address format:
    - 42 characters long
    - Starts with '0x'
    - Contains only valid hexadecimal characters

    Args:
        address: The address to validate

    Returns:
        bool: True if address is valid

    Example:
        >>> validate_ethereum_address('0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
        True
    """
    if not isinstance(address, str):
        return False
    return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))


def validate_hex_data(data: str) -> bool:
    """
    Validate hexadecimal data string.

    Ensures the input is a valid hex string:
    - Starts with '0x'
    - Contains only valid hex characters
    - Has even length (complete bytes)

    Args:
        data: The hex string to validate

    Returns:
        bool: True if data is valid
    """
    if not isinstance(data, str) or not data.startswith("0x"):
        return False
    try:
        # Remove '0x' prefix and check if remaining string is valid hex
        hex_data = data[2:]
        return len(hex_data) % 2 == 0 and all(
            c in "0123456789abcdefABCDEF" for c in hex_data
        )
    except Exception:
        return False


def sanitize_command(command: Union[str, List[str]]) -> List[str]:
    """
    Sanitize command input to prevent injection attacks.

    This function:
    1. Splits string commands safely
    2. Checks for dangerous patterns
    3. Validates command structure

    Args:
        command: Command string or list

    Returns:
        List[str]: Safe command arguments

    Raises:
        ValidationError: If command contains dangerous patterns
    """
    # Convert string command to list
    if isinstance(command, str):
        command = command.split()

    # Dangerous patterns to check for
    dangerous_patterns = [
        r"[;&|]",  # Shell operators
        r">",  # Redirections
        r"<",  # Redirections
        r"\$\(",  # Command substitution
        r"`",  # Backticks
        r"\.\.",  # Directory traversal
        r"sudo",  # Privilege escalation
        r"source",  # Shell sourcing
        r"eval",  # Code evaluation
    ]

    # Check each argument
    for arg in command:
        for pattern in dangerous_patterns:
            if re.search(pattern, arg):
                raise ValidationError(f"Dangerous pattern detected in command: {arg}")

    return command


def validate_environment_vars(env_vars: Dict[str, str]) -> Dict[str, str]:
    """
    Validate and sanitize environment variables.

    Ensures environment variables:
    1. Have valid names (alphanumeric and underscore)
    2. Don't contain dangerous values
    3. Are properly typed

    Args:
        env_vars: Dictionary of environment variables

    Returns:
        Dict[str, str]: Sanitized environment variables
    """
    if not isinstance(env_vars, dict):
        raise ValidationError("Environment variables must be provided as a dictionary")

    sanitized = {}
    for key, value in env_vars.items():
        # Validate key format
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", str(key)):
            raise ValidationError(f"Invalid environment variable name: {key}")

        # Validate value
        str_value = str(value)
        if any(char in str_value for char in ";&|><`$()"):
            raise ValidationError(
                f"Invalid characters in environment value: {key}={value}"
            )

        sanitized[str(key)] = str_value

    return sanitized
