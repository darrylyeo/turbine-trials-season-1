"""
EIP-712 signing for Turbine orders.
"""

import secrets
import time
from typing import Any, Dict, Optional

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak, to_checksum_address

from turbine_client.config import get_settlement_address
from turbine_client.constants import (
    EIP712_DOMAIN_NAME,
    EIP712_DOMAIN_VERSION,
    EIP712_ORDER_TYPE,
)
from turbine_client.exceptions import SignatureError
from turbine_client.types import OrderArgs, SignedOrder


class Signer:
    """EIP-712 signer for Turbine orders."""

    def __init__(self, private_key: str, chain_id: int) -> None:
        """Initialize the signer.

        Args:
            private_key: The private key (hex string with or without 0x prefix).
            chain_id: The chain ID for the EIP-712 domain.
        """
        # Normalize private key
        if not private_key.startswith("0x"):
            private_key = f"0x{private_key}"

        self._account = Account.from_key(private_key)
        self._chain_id = chain_id
        self._settlement_address = get_settlement_address(chain_id)

    @property
    def address(self) -> str:
        """Get the signer's address."""
        return self._account.address

    @property
    def chain_id(self) -> int:
        """Get the chain ID."""
        return self._chain_id

    def get_domain(self) -> Dict[str, Any]:
        """Get the EIP-712 domain for signing.

        Returns:
            The EIP-712 domain dictionary.
        """
        return {
            "name": EIP712_DOMAIN_NAME,
            "version": EIP712_DOMAIN_VERSION,
            "chainId": self._chain_id,
            "verifyingContract": self._settlement_address,
        }

    def _get_domain_for_contract(self, verifying_contract: str) -> Dict[str, Any]:
        """Get the EIP-712 domain with a specific verifying contract.

        Args:
            verifying_contract: The settlement contract address.

        Returns:
            The EIP-712 domain dictionary.
        """
        return {
            "name": EIP712_DOMAIN_NAME,
            "version": EIP712_DOMAIN_VERSION,
            "chainId": self._chain_id,
            "verifyingContract": verifying_contract,
        }

    def sign_order(
        self, order_args: OrderArgs, settlement_address: Optional[str] = None
    ) -> SignedOrder:
        """Sign an order using EIP-712.

        Args:
            order_args: The order arguments.
            settlement_address: Optional settlement contract address for the market.
                               If not provided, uses the default for the chain.

        Returns:
            A signed order ready for submission.

        Raises:
            SignatureError: If signing fails.
        """
        try:
            # Generate nonce if not provided
            nonce = order_args.nonce if order_args.nonce > 0 else self._generate_nonce()

            # Build the order message
            order_message = {
                "marketId": self._normalize_market_id(order_args.market_id),
                "trader": self.address,
                "side": int(order_args.side),
                "outcome": int(order_args.outcome),
                "price": order_args.price,
                "size": order_args.size,
                "nonce": nonce,
                "expiration": order_args.expiration,
                "makerFeeRecipient": to_checksum_address(order_args.maker_fee_recipient),
            }

            # Use provided settlement address or fall back to chain default
            verifying_contract = (
                to_checksum_address(settlement_address)
                if settlement_address
                else self._settlement_address
            )

            # Create typed data for EIP-712 signing
            typed_data = {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"},
                    ],
                    "Order": [
                        {"name": "marketId", "type": "bytes32"},
                        {"name": "trader", "type": "address"},
                        {"name": "side", "type": "uint8"},
                        {"name": "outcome", "type": "uint8"},
                        {"name": "price", "type": "uint256"},
                        {"name": "size", "type": "uint256"},
                        {"name": "nonce", "type": "uint256"},
                        {"name": "expiration", "type": "uint256"},
                        {"name": "makerFeeRecipient", "type": "address"},
                    ],
                },
                "primaryType": "Order",
                "domain": self._get_domain_for_contract(verifying_contract),
                "message": order_message,
            }

            # Sign the typed data
            signed_message = Account.sign_typed_data(
                self._account.key,
                full_message=typed_data,
            )

            # Compute order hash
            order_hash = self._compute_order_hash(typed_data)

            return SignedOrder(
                market_id=order_args.market_id,
                trader=self.address,
                side=int(order_args.side),
                outcome=int(order_args.outcome),
                price=order_args.price,
                size=order_args.size,
                nonce=nonce,
                expiration=order_args.expiration,
                maker_fee_recipient=order_args.maker_fee_recipient,
                signature=signed_message.signature.hex(),
                order_hash=order_hash,
            )
        except Exception as e:
            raise SignatureError(f"Failed to sign order: {e}") from e

    def _normalize_market_id(self, market_id: str) -> bytes:
        """Normalize market ID to bytes32.

        Args:
            market_id: The market ID (hex string).

        Returns:
            The market ID as bytes32.
        """
        # Remove 0x prefix if present
        if market_id.startswith("0x"):
            market_id = market_id[2:]

        # Pad to 32 bytes
        market_id = market_id.zfill(64)

        return bytes.fromhex(market_id)

    def _generate_nonce(self) -> int:
        """Generate a unique nonce that fits in uint64.

        Returns:
            A unique nonce combining timestamp and random value, within uint64 range.
        """
        # Use seconds since epoch (fits in ~32 bits until 2106)
        timestamp = int(time.time())
        # Random 32-bit value for uniqueness
        random_part = secrets.randbelow(2**32)
        # Combine: upper 32 bits = timestamp, lower 32 bits = random
        # This fits in uint64 and ensures uniqueness
        return (timestamp << 32) | random_part

    def _compute_order_hash(self, typed_data: Dict[str, Any]) -> str:
        """Compute the order hash from typed data.

        Args:
            typed_data: The EIP-712 typed data.

        Returns:
            The order hash as a hex string.
        """
        # Encode the typed data and compute keccak256
        encoded = encode_typed_data(full_message=typed_data)
        return f"0x{keccak(encoded.body).hex()}"


def create_signer(private_key: str, chain_id: int) -> Signer:
    """Create a new signer.

    Args:
        private_key: The private key (hex string).
        chain_id: The chain ID.

    Returns:
        A new Signer instance.
    """
    return Signer(private_key, chain_id)
