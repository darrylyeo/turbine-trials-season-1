"""
Helper functions for order building.
"""

from decimal import Decimal, ROUND_DOWN, ROUND_UP
from typing import Union

from turbine_client.constants import MAX_PRICE, MIN_PRICE, PRICE_SCALE, SIZE_DECIMALS
from turbine_client.exceptions import OrderValidationError


def price_to_decimal(price: int) -> Decimal:
    """Convert a scaled price to a decimal.

    Args:
        price: The price scaled by 1e6.

    Returns:
        The price as a Decimal (0.0 to 1.0).

    Example:
        >>> price_to_decimal(500000)
        Decimal('0.5')
    """
    return Decimal(price) / Decimal(PRICE_SCALE)


def decimal_to_price(decimal_price: Union[float, Decimal]) -> int:
    """Convert a decimal price to scaled integer.

    Args:
        decimal_price: The price as a decimal (0.0 to 1.0).

    Returns:
        The price scaled by 1e6.

    Example:
        >>> decimal_to_price(0.5)
        500000
    """
    return int(Decimal(str(decimal_price)) * PRICE_SCALE)


def size_to_shares(size: int) -> Decimal:
    """Convert a scaled size to shares.

    Args:
        size: The size with 6 decimals.

    Returns:
        The number of shares as a Decimal.

    Example:
        >>> size_to_shares(1000000)
        Decimal('1')
    """
    return Decimal(size) / Decimal(10**SIZE_DECIMALS)


def shares_to_size(shares: Union[float, Decimal]) -> int:
    """Convert shares to scaled size.

    Args:
        shares: The number of shares.

    Returns:
        The size with 6 decimals.

    Example:
        >>> shares_to_size(1.5)
        1500000
    """
    return int(Decimal(str(shares)) * Decimal(10**SIZE_DECIMALS))


def validate_price(price: int) -> None:
    """Validate a price value.

    Args:
        price: The price scaled by 1e6.

    Raises:
        OrderValidationError: If the price is invalid.
    """
    if not isinstance(price, int):
        raise OrderValidationError(f"Price must be an integer, got {type(price)}", field="price")
    if price < MIN_PRICE:
        raise OrderValidationError(
            f"Price must be at least {MIN_PRICE} (0.0001%), got {price}",
            field="price",
        )
    if price > MAX_PRICE:
        raise OrderValidationError(
            f"Price must be at most {MAX_PRICE} (99.9999%), got {price}",
            field="price",
        )


def validate_size(size: int) -> None:
    """Validate a size value.

    Args:
        size: The size with 6 decimals.

    Raises:
        OrderValidationError: If the size is invalid.
    """
    if not isinstance(size, int):
        raise OrderValidationError(f"Size must be an integer, got {type(size)}", field="size")
    if size <= 0:
        raise OrderValidationError(f"Size must be positive, got {size}", field="size")


def round_price_down(decimal_price: Union[float, Decimal], tick_size: float = 0.0001) -> Decimal:
    """Round a decimal price down to the nearest tick.

    Args:
        decimal_price: The price as a decimal.
        tick_size: The minimum price increment.

    Returns:
        The rounded price.
    """
    tick = Decimal(str(tick_size))
    price = Decimal(str(decimal_price))
    return (price / tick).quantize(Decimal("1"), rounding=ROUND_DOWN) * tick


def round_price_up(decimal_price: Union[float, Decimal], tick_size: float = 0.0001) -> Decimal:
    """Round a decimal price up to the nearest tick.

    Args:
        decimal_price: The price as a decimal.
        tick_size: The minimum price increment.

    Returns:
        The rounded price.
    """
    tick = Decimal(str(tick_size))
    price = Decimal(str(decimal_price))
    return (price / tick).quantize(Decimal("1"), rounding=ROUND_UP) * tick


def round_size_down(shares: Union[float, Decimal], min_size: float = 0.000001) -> Decimal:
    """Round a size down to the minimum increment.

    Args:
        shares: The number of shares.
        min_size: The minimum size increment.

    Returns:
        The rounded size.
    """
    increment = Decimal(str(min_size))
    size = Decimal(str(shares))
    return (size / increment).quantize(Decimal("1"), rounding=ROUND_DOWN) * increment


def calculate_cost(price: int, size: int) -> int:
    """Calculate the cost of an order.

    Args:
        price: The price scaled by 1e6.
        size: The size with 6 decimals.

    Returns:
        The cost in USDC (6 decimals).

    Example:
        >>> calculate_cost(500000, 1000000)  # 50% * 1 share
        500000  # 0.5 USDC
    """
    # cost = price * size / 1e6
    return (price * size) // PRICE_SCALE


def calculate_payout(size: int) -> int:
    """Calculate the payout if the outcome wins.

    Args:
        size: The size with 6 decimals.

    Returns:
        The payout in USDC (6 decimals).

    Example:
        >>> calculate_payout(1000000)  # 1 share
        1000000  # 1 USDC
    """
    return size


def calculate_profit(price: int, size: int) -> int:
    """Calculate the potential profit of an order.

    Args:
        price: The price scaled by 1e6.
        size: The size with 6 decimals.

    Returns:
        The potential profit in USDC (6 decimals).

    Example:
        >>> calculate_profit(500000, 1000000)  # 50% * 1 share
        500000  # 0.5 USDC profit if wins
    """
    cost = calculate_cost(price, size)
    payout = calculate_payout(size)
    return payout - cost
