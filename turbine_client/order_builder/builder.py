"""
Order builder for creating and signing orders.
"""

import time
from typing import Optional

from turbine_client.exceptions import OrderValidationError
from turbine_client.order_builder.helpers import validate_price, validate_size
from turbine_client.signer import Signer
from turbine_client.types import OrderArgs, Outcome, Side, SignedOrder


class OrderBuilder:
    """Builder for creating and signing orders."""

    def __init__(self, signer: Signer) -> None:
        """Initialize the order builder.

        Args:
            signer: The signer for signing orders.
        """
        self._signer = signer

    @property
    def address(self) -> str:
        """Get the trader address."""
        return self._signer.address

    @property
    def chain_id(self) -> int:
        """Get the chain ID."""
        return self._signer.chain_id

    def create_order(
        self,
        market_id: str,
        side: Side,
        outcome: Outcome,
        price: int,
        size: int,
        expiration: Optional[int] = None,
        nonce: int = 0,
        maker_fee_recipient: Optional[str] = None,
        settlement_address: Optional[str] = None,
    ) -> SignedOrder:
        """Create and sign an order.

        Args:
            market_id: The market ID (bytes32 hex string).
            side: BUY or SELL.
            outcome: YES or NO.
            price: Price scaled by 1e6 (1 to 999999).
            size: Size with 6 decimals.
            expiration: Unix timestamp for order expiration.
                       Defaults to 1 hour from now.
            nonce: Order nonce. Auto-generated if 0.
            maker_fee_recipient: Address to receive maker fees.
                                Defaults to trader's own address.
            settlement_address: The market's settlement contract address.

        Returns:
            A signed order ready for submission.

        Raises:
            OrderValidationError: If order parameters are invalid.
        """
        # Validate inputs
        self._validate_market_id(market_id)
        validate_price(price)
        validate_size(size)

        # Default expiration to 1 hour from now
        if expiration is None:
            expiration = int(time.time()) + 3600

        # Default maker_fee_recipient to trader's own address
        if maker_fee_recipient is None:
            maker_fee_recipient = self._signer.address

        # Create order args
        order_args = OrderArgs(
            market_id=market_id,
            side=side,
            outcome=outcome,
            price=price,
            size=size,
            expiration=expiration,
            nonce=nonce,
            maker_fee_recipient=maker_fee_recipient,
        )

        # Sign and return
        return self._signer.sign_order(order_args, settlement_address=settlement_address)

    def create_order_from_args(
        self, order_args: OrderArgs, settlement_address: Optional[str] = None
    ) -> SignedOrder:
        """Create and sign an order from OrderArgs.

        Args:
            order_args: The order arguments.
            settlement_address: The market's settlement contract address.

        Returns:
            A signed order ready for submission.
        """
        # Validate
        self._validate_market_id(order_args.market_id)
        validate_price(order_args.price)
        validate_size(order_args.size)

        # Sign and return
        return self._signer.sign_order(order_args, settlement_address=settlement_address)

    def create_limit_buy(
        self,
        market_id: str,
        outcome: Outcome,
        price: int,
        size: int,
        expiration: Optional[int] = None,
        settlement_address: Optional[str] = None,
    ) -> SignedOrder:
        """Create a limit buy order.

        Args:
            market_id: The market ID.
            outcome: YES or NO.
            price: Price scaled by 1e6.
            size: Size with 6 decimals.
            expiration: Unix timestamp for expiration.
            settlement_address: The market's settlement contract address.

        Returns:
            A signed buy order.
        """
        return self.create_order(
            market_id=market_id,
            side=Side.BUY,
            outcome=outcome,
            price=price,
            size=size,
            expiration=expiration,
            settlement_address=settlement_address,
        )

    def create_limit_sell(
        self,
        market_id: str,
        outcome: Outcome,
        price: int,
        size: int,
        expiration: Optional[int] = None,
        settlement_address: Optional[str] = None,
    ) -> SignedOrder:
        """Create a limit sell order.

        Args:
            market_id: The market ID.
            outcome: YES or NO.
            price: Price scaled by 1e6.
            size: Size with 6 decimals.
            expiration: Unix timestamp for expiration.
            settlement_address: The market's settlement contract address.

        Returns:
            A signed sell order.
        """
        return self.create_order(
            market_id=market_id,
            side=Side.SELL,
            outcome=outcome,
            price=price,
            size=size,
            expiration=expiration,
            settlement_address=settlement_address,
        )

    def _validate_market_id(self, market_id: str) -> None:
        """Validate a market ID.

        Args:
            market_id: The market ID.

        Raises:
            OrderValidationError: If the market ID is invalid.
        """
        if not market_id:
            raise OrderValidationError("market_id is required", field="market_id")

        # Remove 0x prefix for length check
        clean_id = market_id[2:] if market_id.startswith("0x") else market_id

        # Should be valid hex
        try:
            int(clean_id, 16)
        except ValueError:
            raise OrderValidationError(
                f"market_id must be a valid hex string, got {market_id}",
                field="market_id",
            )

        # Should be at most 64 characters (32 bytes)
        if len(clean_id) > 64:
            raise OrderValidationError(
                f"market_id too long: {len(clean_id)} chars, max 64",
                field="market_id",
            )
