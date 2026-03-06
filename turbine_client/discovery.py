"""
API-based position discovery for the Turbine SDK.

Uses the Turbine API endpoints for position discovery instead of direct
on-chain RPC calls. This eliminates the need for any RPC connection.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Quick market assets to scan
QUICK_MARKET_ASSETS = ["BTC", "ETH", "SOL"]


@dataclass
class ClaimablePosition:
    """A resolved market position that can be redeemed for USDC."""
    market_id: str
    contract_address: str
    source: str
    condition_id: str
    winning_outcome: int  # 0=YES, 1=NO
    winning_balance: int  # raw amount (6 decimals)
    payout_usdc: float    # human-readable USDC value

    @property
    def outcome_label(self) -> str:
        return "YES" if self.winning_outcome == 0 else "NO"


@dataclass
class MergeablePosition:
    """A market where paired YES+NO tokens can be merged back to USDC."""
    market_id: str
    contract_address: str
    source: str
    condition_id: str
    yes_balance: int
    no_balance: int
    mergeable_amount: int  # min(yes, no)
    merge_usdc: float      # human-readable USDC value


@dataclass
class DiscoveryResult:
    """Result of position discovery."""
    claimable: List[ClaimablePosition] = field(default_factory=list)
    mergeable: List[MergeablePosition] = field(default_factory=list)
    markets_scanned: int = 0
    total_claimable_usdc: float = 0.0
    total_mergeable_usdc: float = 0.0

    @property
    def total_usdc(self) -> float:
        return self.total_claimable_usdc + self.total_mergeable_usdc


def discover_positions(
    wallet_address: str,
    api_base_url: str,
    http_client: Any,
    chain_id: int = 137,
    **kwargs,
) -> DiscoveryResult:
    """Discover all claimable positions via the Turbine API.

    Uses the /users/:address/claimable endpoint for reliable position discovery
    without requiring any direct RPC connection.

    Args:
        wallet_address: The wallet address to check.
        api_base_url: The API base URL (unused, kept for compatibility).
        http_client: HTTP client for API calls.
        chain_id: The chain ID.
        **kwargs: Accepts and ignores legacy parameters (w3, ctf_address) for
                  backward compatibility.

    Returns:
        DiscoveryResult with claimable positions.
    """
    result = DiscoveryResult()

    try:
        endpoint = f"/api/v1/users/{wallet_address}/claimable"
        params = {"chain_id": str(chain_id), "verify": "true"}
        response = http_client.get(endpoint, params=params, authenticated=True)

        claimable_items = response.get("claimable", [])
        result.markets_scanned = response.get("count", len(claimable_items))

        for item in claimable_items:
            balance_str = item.get("balance", "0")
            balance = int(balance_str) if balance_str else 0

            if balance <= 0:
                continue

            payout_usdc = balance / 1_000_000
            winning_outcome = 0 if item.get("outcome_label") == "YES" else 1

            result.claimable.append(ClaimablePosition(
                market_id=item.get("market_id", ""),
                contract_address=item.get("contract_address", ""),
                source="api-claimable",
                condition_id="",  # Not provided by claimable endpoint
                winning_outcome=winning_outcome,
                winning_balance=balance,
                payout_usdc=payout_usdc,
            ))
            result.total_claimable_usdc += payout_usdc

    except Exception as e:
        logger.warning("Failed to fetch claimable positions from API: %s", e)

    logger.info(
        "Discovery complete: %d claimable ($%.2f), %d markets scanned",
        len(result.claimable), result.total_claimable_usdc,
        result.markets_scanned,
    )

    return result
