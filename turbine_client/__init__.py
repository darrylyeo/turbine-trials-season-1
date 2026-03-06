"""
Turbine Python Client

A Python client for market makers to interact with the Turbine CLOB prediction markets API.
"""

from turbine_client.client import TurbineClient
from turbine_client.discovery import (
    ClaimablePosition as DiscoveredClaimable,
    DiscoveryResult,
    MergeablePosition,
)
from turbine_client.types import (
    AssetPrice,
    ChainStats,
    ClaimablePosition,
    FailedClaim,
    FailedTrade,
    Holder,
    Market,
    MarketStats,
    OrderArgs,
    OrderBookSnapshot,
    Outcome,
    PendingClaim,
    PendingTrade,
    PermitSignature,
    PlatformStats,
    Position,
    PriceLevel,
    QuickMarket,
    Resolution,
    SettlementStatus,
    Side,
    SignedOrder,
    Trade,
    UserStats,
)
from turbine_client.ws.client import TurbineWSClient
from turbine_client.exceptions import (
    AuthenticationError,
    OrderValidationError,
    SignatureError,
    TurbineApiError,
    TurbineError,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    "TurbineClient",
    "TurbineWSClient",
    # Types
    "AssetPrice",
    "ChainStats",
    "ClaimablePosition",
    "FailedClaim",
    "FailedTrade",
    "Holder",
    "Market",
    "MarketStats",
    "OrderArgs",
    "OrderBookSnapshot",
    "Outcome",
    "PendingClaim",
    "PendingTrade",
    "PermitSignature",
    "PlatformStats",
    "Position",
    "PriceLevel",
    "QuickMarket",
    "Resolution",
    "SettlementStatus",
    "Side",
    "SignedOrder",
    "Trade",
    "UserStats",
    # Discovery types
    "DiscoveryResult",
    "DiscoveredClaimable",
    "MergeablePosition",
    # Exceptions
    "TurbineError",
    "TurbineApiError",
    "OrderValidationError",
    "SignatureError",
    "AuthenticationError",
]
