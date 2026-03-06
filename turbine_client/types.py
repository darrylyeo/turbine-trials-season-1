"""
Data types and models for the Turbine Python client.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional


class Side(IntEnum):
    """Order side: BUY or SELL."""

    BUY = 0
    SELL = 1


class Outcome(IntEnum):
    """Market outcome: YES or NO."""

    YES = 0
    NO = 1


@dataclass
class OrderArgs:
    """Arguments for creating a new order."""

    market_id: str
    side: Side
    outcome: Outcome
    price: int  # Price scaled by 1e6 (0 to 1,000,000)
    size: int  # Size in 6 decimals
    expiration: int  # Unix timestamp
    nonce: int = 0  # Auto-generated if 0
    maker_fee_recipient: str = "0x0000000000000000000000000000000000000000"

    def __post_init__(self) -> None:
        """Validate order arguments."""
        if not (1 <= self.price <= 999_999):
            raise ValueError(f"Price must be between 1 and 999999, got {self.price}")
        if self.size <= 0:
            raise ValueError(f"Size must be positive, got {self.size}")
        if self.expiration <= 0:
            raise ValueError(f"Expiration must be positive, got {self.expiration}")


@dataclass
class PermitSignature:
    """EIP-2612 permit signature for gasless USDC approval."""

    nonce: int  # The nonce used when signing (must match on-chain)
    value: int  # Amount approved
    deadline: int  # Expiration timestamp
    v: int
    r: str  # Hex string with 0x prefix
    s: str  # Hex string with 0x prefix

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API submission."""
        return {
            "nonce": self.nonce,
            "value": self.value,
            "deadline": self.deadline,
            "v": self.v,
            "r": self.r,
            "s": self.s,
        }


@dataclass
class SignedOrder:
    """A signed order ready for submission."""

    market_id: str
    trader: str
    side: int
    outcome: int
    price: int
    size: int
    nonce: int
    expiration: int
    maker_fee_recipient: str
    signature: str
    order_hash: str
    permit_signature: Optional["PermitSignature"] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API submission."""
        # Ensure signature has 0x prefix
        sig = self.signature if self.signature.startswith("0x") else f"0x{self.signature}"
        result = {
            "order": {
                "marketId": self.market_id,
                "trader": self.trader,
                "side": self.side,
                "outcome": self.outcome,
                "price": self.price,
                "size": self.size,
                "nonce": self.nonce,
                "expiration": self.expiration,
                "makerFeeRecipient": self.maker_fee_recipient,
            },
            "signature": sig,
        }
        if self.permit_signature:
            result["permitSignature"] = self.permit_signature.to_dict()
        return result


@dataclass
class PriceLevel:
    """A price level in the orderbook."""

    price: int
    size: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PriceLevel":
        """Create from API response dictionary."""
        return cls(
            price=int(data["price"]),
            size=int(data["size"]),
        )


@dataclass
class OrderBookSnapshot:
    """A snapshot of the orderbook for a market."""

    market_id: str
    bids: List[PriceLevel]
    asks: List[PriceLevel]
    last_update: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderBookSnapshot":
        """Create from API response dictionary."""
        return cls(
            market_id=data.get("marketId", ""),
            bids=[PriceLevel.from_dict(b) for b in data.get("bids", [])],
            asks=[PriceLevel.from_dict(a) for a in data.get("asks", [])],
            last_update=data.get("lastUpdate", 0),
        )


@dataclass
class Trade:
    """A trade execution."""

    id: int
    market_id: str
    buyer: str
    seller: str
    price: int
    size: int
    outcome: int
    timestamp: int
    tx_hash: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trade":
        """Create from API response dictionary."""
        return cls(
            id=int(data.get("id", 0)),
            market_id=data.get("marketId", ""),
            buyer=data.get("buyer", ""),
            seller=data.get("seller", ""),
            price=int(data.get("price", 0)),
            size=int(data.get("size", 0)),
            outcome=int(data.get("outcome", 0)),
            timestamp=int(data.get("timestamp", 0)),
            tx_hash=data.get("txHash", ""),
        )


@dataclass
class Position:
    """A user's position in a market."""

    id: int
    market_id: str
    user_address: str
    yes_shares: int
    no_shares: int
    yes_cost: int
    no_cost: int
    yes_revenue: int
    no_revenue: int
    total_invested: int
    total_cost: int
    total_revenue: int
    last_updated: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Position":
        """Create from API response dictionary."""
        return cls(
            id=int(data.get("id", 0)),
            market_id=data.get("marketId", ""),
            user_address=data.get("userAddress", ""),
            yes_shares=int(data.get("yesShares", 0)),
            no_shares=int(data.get("noShares", 0)),
            yes_cost=int(data.get("yesCost", 0)),
            no_cost=int(data.get("noCost", 0)),
            yes_revenue=int(data.get("yesRevenue", 0)),
            no_revenue=int(data.get("noRevenue", 0)),
            total_invested=int(data.get("totalInvested", 0)),
            total_cost=int(data.get("totalCost", 0)),
            total_revenue=int(data.get("totalRevenue", 0)),
            last_updated=int(data.get("lastUpdated", 0)),
        )


@dataclass
class Holder:
    """A top holder in a market."""

    user_address: str
    yes_shares: int
    no_shares: int
    total_invested: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Holder":
        """Create from API response dictionary."""
        return cls(
            user_address=data.get("userAddress", ""),
            yes_shares=int(data.get("yesShares", 0)),
            no_shares=int(data.get("noShares", 0)),
            total_invested=int(data.get("totalInvested", 0)),
        )


@dataclass
class Market:
    """A prediction market."""

    id: str
    chain_id: int
    contract_address: str
    settlement_address: str
    question: str
    description: str
    category: str
    expiration: int
    maker: str
    resolved: bool
    winning_outcome: Optional[int]
    volume: int
    created_at: int
    updated_at: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Market":
        """Create from API response dictionary."""
        return cls(
            id=data.get("id", ""),
            chain_id=int(data.get("chainId", 0)),
            contract_address=data.get("contractAddress", ""),
            settlement_address=data.get("settlementAddress", ""),
            question=data.get("question", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            expiration=int(data.get("expiration", 0)),
            maker=data.get("maker", ""),
            resolved=data.get("resolved", False),
            winning_outcome=data.get("winningOutcome"),
            volume=int(data.get("volume", 0)),
            created_at=int(data.get("createdAt", 0)),
            updated_at=int(data.get("updatedAt", 0)),
        )


@dataclass
class MarketStats:
    """Statistics for a market."""

    market_id: str
    contract_address: str
    last_price: int
    total_volume: int
    volume_24h: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketStats":
        """Create from API response dictionary."""
        return cls(
            market_id=data.get("marketId", ""),
            contract_address=data.get("contractAddress", ""),
            last_price=int(data.get("lastPrice", 0)),
            total_volume=int(data.get("totalVolume", 0)),
            volume_24h=int(data.get("volume24h", 0)),
        )


@dataclass
class ChainStats:
    """Statistics for a single chain."""

    chain_id: int
    total_volume: int
    total_trades: int
    updated_at: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChainStats":
        """Create from API response dictionary."""
        return cls(
            chain_id=int(data.get("chain_id", 0)),
            total_volume=int(data.get("total_volume", 0)),
            total_trades=int(data.get("total_trades", 0)),
            updated_at=int(data.get("updated_at", 0)),
        )


@dataclass
class PlatformStats:
    """Platform-wide statistics."""

    chains: List["ChainStats"]
    total_volume: int
    total_trades: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlatformStats":
        """Create from API response dictionary."""
        return cls(
            chains=[ChainStats.from_dict(c) for c in data.get("chains", [])],
            total_volume=int(data.get("total_volume", 0)),
            total_trades=int(data.get("total_trades", 0)),
        )


@dataclass
class QuickMarket:
    """A quick market (15-minute BTC/ETH markets)."""

    id: int
    market_id: str
    asset: str
    interval_minutes: int
    start_price: int
    end_price: Optional[int]
    start_time: int
    end_time: int
    resolved: bool
    outcome: Optional[int]
    price_source: str
    created_at: int
    contract_address: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuickMarket":
        """Create from API response dictionary."""
        return cls(
            id=int(data.get("id", 0)),
            market_id=data.get("marketId", ""),
            asset=data.get("asset", ""),
            interval_minutes=int(data.get("intervalMinutes", 0)),
            start_price=int(data.get("startPrice", 0)),
            end_price=data.get("endPrice"),
            start_time=int(data.get("startTime", 0)),
            end_time=int(data.get("endTime", 0)),
            resolved=data.get("resolved", False),
            outcome=data.get("outcome"),
            price_source=data.get("priceSource", ""),
            created_at=int(data.get("createdAt", 0)),
            contract_address=data.get("contractAddress", ""),
        )


@dataclass
class Resolution:
    """Market resolution status."""

    market_id: str
    assertion_id: str
    outcome: int
    resolved: bool
    timestamp: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resolution":
        """Create from API response dictionary."""
        return cls(
            market_id=data.get("marketId", ""),
            assertion_id=data.get("assertionId", ""),
            outcome=int(data.get("winningOutcome", data.get("outcome", 0))),
            resolved=data.get("resolved", False),
            timestamp=int(data.get("timestamp", 0)),
        )


@dataclass
class FailedTrade:
    """A failed trade."""

    market_id: str
    tx_hash: str
    buyer_address: str
    seller_address: str
    fill_size: int
    fill_price: int
    reason: str
    timestamp: str
    batch_index: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailedTrade":
        """Create from API response dictionary."""
        return cls(
            market_id=data.get("marketId", ""),
            tx_hash=data.get("txHash", ""),
            buyer_address=data.get("buyerAddress", ""),
            seller_address=data.get("sellerAddress", ""),
            fill_size=int(data.get("fillSize", 0)),
            fill_price=int(data.get("fillPrice", 0)),
            reason=data.get("reason", ""),
            timestamp=data.get("timestamp", ""),
            batch_index=int(data.get("batchIndex", 0)),
        )


@dataclass
class PendingTrade:
    """A pending trade."""

    market_id: str
    tx_hash: str
    buyer_address: str
    seller_address: str
    fill_size: int
    fill_price: int
    timestamp: str
    is_batch: bool
    batch_index: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PendingTrade":
        """Create from API response dictionary."""
        return cls(
            market_id=data.get("marketId", ""),
            tx_hash=data.get("txHash", ""),
            buyer_address=data.get("buyerAddress", ""),
            seller_address=data.get("sellerAddress", ""),
            fill_size=int(data.get("fillSize", 0)),
            fill_price=int(data.get("fillPrice", 0)),
            timestamp=data.get("timestamp", ""),
            is_batch=data.get("isBatch", False),
            batch_index=int(data.get("batchIndex", 0)),
        )


@dataclass
class ClaimablePosition:
    """A resolved market where the user has winning tokens to claim."""

    market_id: str
    contract_address: str
    outcome_label: str  # "YES" or "NO"
    balance: int  # Raw token units (6 decimals)
    payout: str  # Human-readable payout (e.g. "10.50")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClaimablePosition":
        return cls(
            market_id=data.get("market_id", ""),
            contract_address=data.get("contract_address", ""),
            outcome_label=data.get("outcome_label", ""),
            balance=int(data.get("balance", 0)),
            payout=data.get("payout", "0.00"),
        )

    @property
    def payout_float(self) -> float:
        return self.balance / 1_000_000


@dataclass
class FailedClaim:
    """A failed claim."""

    tx_hash: str
    user_address: str
    market_address: str
    market_id: str
    payout: int
    winning_outcome: int
    submitted_at: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailedClaim":
        """Create from API response dictionary."""
        return cls(
            tx_hash=data.get("txHash", ""),
            user_address=data.get("userAddress", ""),
            market_address=data.get("marketAddress", ""),
            market_id=data.get("marketId", ""),
            payout=int(data.get("payout", 0)),
            winning_outcome=int(data.get("winningOutcome", 0)),
            submitted_at=int(data.get("submittedAt", 0)),
        )


@dataclass
class PendingClaim:
    """A pending claim."""

    tx_hash: str
    user_address: str
    market_address: str
    market_id: str
    payout: int
    winning_outcome: int
    submitted_at: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PendingClaim":
        """Create from API response dictionary."""
        return cls(
            tx_hash=data.get("txHash", ""),
            user_address=data.get("userAddress", ""),
            market_address=data.get("marketAddress", ""),
            market_id=data.get("marketId", ""),
            payout=int(data.get("payout", 0)),
            winning_outcome=int(data.get("winningOutcome", 0)),
            submitted_at=int(data.get("submittedAt", 0)),
        )


@dataclass
class SettlementStatus:
    """Settlement status for a transaction."""

    found: bool
    tx_hash: str
    status: str
    error: str
    market_id: str
    buyer_address: str
    seller_address: str
    fill_size: int
    fill_price: int
    timestamp: str
    is_batch: bool
    batch_index: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SettlementStatus":
        """Create from API response dictionary."""
        return cls(
            found=data.get("found", False),
            tx_hash=data.get("txHash", ""),
            status=data.get("status", ""),
            error=data.get("error", ""),
            market_id=data.get("marketId", ""),
            buyer_address=data.get("buyerAddress", ""),
            seller_address=data.get("sellerAddress", ""),
            fill_size=int(data.get("fillSize", 0)),
            fill_price=int(data.get("fillPrice", 0)),
            timestamp=data.get("timestamp", ""),
            is_batch=data.get("isBatch", False),
            batch_index=int(data.get("batchIndex", 0)),
        )


@dataclass
class AssetPrice:
    """Current price for an asset."""

    price: float
    timestamp: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetPrice":
        """Create from API response dictionary."""
        return cls(
            price=float(data.get("price", 0)),
            timestamp=int(data.get("timestamp", 0)),
        )


@dataclass
class Order:
    """An order on the orderbook."""

    order_hash: str
    market_id: str
    trader: str
    side: int
    outcome: int
    price: int
    size: int
    filled_size: int
    remaining_size: int
    nonce: int
    expiration: int
    status: str
    created_at: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        """Create from API response dictionary."""
        return cls(
            order_hash=data.get("orderHash", ""),
            market_id=data.get("marketId", ""),
            trader=data.get("trader", ""),
            side=int(data.get("side", 0)),
            outcome=int(data.get("outcome", 0)),
            price=int(data.get("price", 0)),
            size=int(data.get("size", 0)),
            filled_size=int(data.get("filledSize", 0)),
            remaining_size=int(data.get("remainingSize", 0)),
            nonce=int(data.get("nonce", 0)),
            expiration=int(data.get("expiration", 0)),
            status=data.get("status", ""),
            created_at=int(data.get("createdAt", 0)),
        )


@dataclass
class UserActivity:
    """User trading activity."""

    address: str
    total_trades: int
    total_volume: int
    pnl: int
    markets_traded: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserActivity":
        """Create from API response dictionary."""
        return cls(
            address=data.get("address", ""),
            total_trades=int(data.get("totalTrades", 0)),
            total_volume=int(data.get("totalVolume", 0)),
            pnl=int(data.get("pnl", 0)),
            markets_traded=int(data.get("marketsTraded", 0)),
        )


@dataclass
class UserStats:
    """User statistics."""

    user_address: str
    total_cost: int  # Total USDC spent on positions (6 decimals)
    total_invested: int  # Total USDC invested in positions (6 decimals)
    position_value: int  # Current value of all positions (6 decimals)
    pnl: int  # Profit/Loss (6 decimals)
    pnl_percentage: float  # PNL as percentage

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserStats":
        """Create from API response dictionary."""
        return cls(
            user_address=data.get("user_address", ""),
            total_cost=int(data.get("total_cost", 0)),
            total_invested=int(data.get("total_invested", 0)),
            position_value=int(data.get("position_value", 0)),
            pnl=int(data.get("pnl", 0)),
            pnl_percentage=float(data.get("pnl_percentage", 0.0)),
        )


# WebSocket message types
@dataclass
class WSMessage:
    """Base WebSocket message."""

    type: str
    market_id: Optional[str] = None
    data: Any = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WSMessage":
        """Create from WebSocket message dictionary."""
        return cls(
            type=data.get("type", ""),
            market_id=data.get("marketId"),
            data=data.get("data"),
        )


@dataclass
class OrderBookUpdate(WSMessage):
    """WebSocket orderbook update message."""

    @property
    def orderbook(self) -> Optional[OrderBookSnapshot]:
        """Get the orderbook snapshot from the message."""
        if self.data and isinstance(self.data, dict):
            return OrderBookSnapshot.from_dict({**self.data, "marketId": self.market_id})
        return None


@dataclass
class TradeUpdate(WSMessage):
    """WebSocket trade update message."""

    @property
    def trade(self) -> Optional[Trade]:
        """Get the trade from the message."""
        if self.data and isinstance(self.data, dict):
            return Trade.from_dict({**self.data, "marketId": self.market_id})
        return None


@dataclass
class QuickMarketUpdate(WSMessage):
    """WebSocket quick market update message."""

    @property
    def quick_market(self) -> Optional[QuickMarket]:
        """Get the quick market from the message."""
        if self.data and isinstance(self.data, dict):
            return QuickMarket.from_dict(self.data)
        return None
