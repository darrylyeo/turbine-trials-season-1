"""
Utility functions for the Turbine Python client.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

from eth_utils import is_address, to_checksum_address

from turbine_client.constants import PRICE_SCALE


def load_private_key_from_env(env_var: str = "TURBINE_PRIVATE_KEY") -> Optional[str]:
    """Load a private key from an environment variable.

    Args:
        env_var: The environment variable name.

    Returns:
        The private key, or None if not set.
    """
    key = os.environ.get(env_var)
    if key:
        # Normalize to include 0x prefix
        if not key.startswith("0x"):
            key = f"0x{key}"
    return key


def load_api_credentials_from_env(
    key_id_var: str = "TURBINE_API_KEY_ID",
    private_key_var: str = "TURBINE_API_PRIVATE_KEY",
) -> Tuple[Optional[str], Optional[str]]:
    """Load API credentials from environment variables.

    Args:
        key_id_var: The environment variable for the key ID.
        private_key_var: The environment variable for the private key.

    Returns:
        A tuple of (key_id, private_key), either may be None.
    """
    return (
        os.environ.get(key_id_var),
        os.environ.get(private_key_var),
    )


def validate_address(address: str) -> str:
    """Validate and checksum an Ethereum address.

    Args:
        address: The address to validate.

    Returns:
        The checksummed address.

    Raises:
        ValueError: If the address is invalid.
    """
    if not is_address(address):
        raise ValueError(f"Invalid Ethereum address: {address}")
    return to_checksum_address(address)


def format_price(price: int) -> str:
    """Format a scaled price for display.

    Args:
        price: The price scaled by 1e6.

    Returns:
        The price as a percentage string.

    Example:
        >>> format_price(500000)
        '50.00%'
    """
    percentage = (price / PRICE_SCALE) * 100
    return f"{percentage:.2f}%"


def format_size(size: int) -> str:
    """Format a size for display.

    Args:
        size: The size with 6 decimals.

    Returns:
        The size as a string with appropriate formatting.

    Example:
        >>> format_size(1500000)
        '1.50'
    """
    shares = size / 1_000_000
    if shares >= 1000:
        return f"{shares:,.0f}"
    elif shares >= 1:
        return f"{shares:.2f}"
    else:
        return f"{shares:.6f}".rstrip("0").rstrip(".")


def format_usdc(amount: int) -> str:
    """Format a USDC amount for display.

    Args:
        amount: The amount with 6 decimals.

    Returns:
        The amount as a dollar string.

    Example:
        >>> format_usdc(1500000)
        '$1.50'
    """
    dollars = amount / 1_000_000
    if dollars >= 1000:
        return f"${dollars:,.2f}"
    elif dollars >= 0.01:
        return f"${dollars:.2f}"
    else:
        return f"${dollars:.6f}".rstrip("0").rstrip(".")


def parse_market_id(market_id: str) -> bytes:
    """Parse a market ID string to bytes32.

    Args:
        market_id: The market ID as a hex string.

    Returns:
        The market ID as 32 bytes.
    """
    if market_id.startswith("0x"):
        market_id = market_id[2:]
    # Pad to 64 characters (32 bytes)
    market_id = market_id.zfill(64)
    return bytes.fromhex(market_id)


def market_id_to_hex(market_id: bytes) -> str:
    """Convert a bytes32 market ID to hex string.

    Args:
        market_id: The market ID as bytes.

    Returns:
        The market ID as a hex string with 0x prefix.
    """
    return f"0x{market_id.hex()}"


def calculate_implied_probability(price: int) -> float:
    """Calculate implied probability from a price.

    Args:
        price: The price scaled by 1e6.

    Returns:
        The implied probability (0.0 to 1.0).

    Example:
        >>> calculate_implied_probability(750000)
        0.75
    """
    return price / PRICE_SCALE


def calculate_odds(price: int) -> float:
    """Calculate decimal odds from a price.

    Args:
        price: The price scaled by 1e6.

    Returns:
        The decimal odds.

    Example:
        >>> calculate_odds(500000)  # 50%
        2.0
        >>> calculate_odds(250000)  # 25%
        4.0
    """
    if price <= 0:
        return float("inf")
    return PRICE_SCALE / price


def calculate_american_odds(price: int) -> int:
    """Calculate American odds from a price.

    Args:
        price: The price scaled by 1e6.

    Returns:
        The American odds (positive or negative).

    Example:
        >>> calculate_american_odds(500000)  # 50%
        -100
        >>> calculate_american_odds(250000)  # 25%
        300
    """
    probability = price / PRICE_SCALE
    if probability >= 0.5:
        return int(-100 * probability / (1 - probability))
    else:
        return int(100 * (1 - probability) / probability)


def dict_to_camel_case(d: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary keys from snake_case to camelCase.

    Args:
        d: The dictionary with snake_case keys.

    Returns:
        A new dictionary with camelCase keys.
    """
    result = {}
    for key, value in d.items():
        # Convert snake_case to camelCase
        parts = key.split("_")
        camel_key = parts[0] + "".join(p.capitalize() for p in parts[1:])
        if isinstance(value, dict):
            result[camel_key] = dict_to_camel_case(value)
        elif isinstance(value, list):
            result[camel_key] = [
                dict_to_camel_case(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[camel_key] = value
    return result


def dict_to_snake_case(d: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary keys from camelCase to snake_case.

    Args:
        d: The dictionary with camelCase keys.

    Returns:
        A new dictionary with snake_case keys.
    """
    import re

    def to_snake(name: str) -> str:
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    result = {}
    for key, value in d.items():
        snake_key = to_snake(key)
        if isinstance(value, dict):
            result[snake_key] = dict_to_snake_case(value)
        elif isinstance(value, list):
            result[snake_key] = [
                dict_to_snake_case(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[snake_key] = value
    return result
