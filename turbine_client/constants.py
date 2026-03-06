"""
Constants for the Turbine Python client.
"""

# Chain IDs
BASE_SEPOLIA = 84532
POLYGON_MAINNET = 137
AVALANCHE_MAINNET = 43114

# Zero address
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Price scaling (1e6)
PRICE_SCALE = 1_000_000
MIN_PRICE = 1
MAX_PRICE = 999_999

# Size scaling (6 decimals)
SIZE_DECIMALS = 6

# API endpoints
ENDPOINTS = {
    # Health
    "health": "/health",

    # Public endpoints (no auth required for GET)
    "markets": "/api/v1/markets",
    "orderbook": "/api/v1/orderbook/{market_id}",
    "trades": "/api/v1/trades/{market_id}",
    "stats": "/api/v1/stats/{market_id}",
    "platform_stats": "/api/v1/platform/stats",
    "holders": "/api/v1/holders/{market_id}",
    "resolution": "/api/v1/resolution/{market_id}",

    # Failed/Pending tracking
    "failed_trades": "/api/v1/failed-trades",
    "pending_trades": "/api/v1/pending-trades",
    "failed_claims": "/api/v1/failed-claims",
    "pending_claims": "/api/v1/pending-claims",
    "settlement_status": "/api/v1/settlements/{tx_hash}",

    # Quick markets
    "quick_market": "/api/v1/quick-markets/{asset}",
    "quick_market_history": "/api/v1/quick-markets/{asset}/history",
    "quick_market_price": "/api/v1/quick-markets/{asset}/price",
    "quick_market_all": "/api/v1/quick-markets/{asset}/all",
    "quick_market_price_history": "/api/v1/quick-markets/{asset}/price-history",

    # Authenticated endpoints (bearer token)
    "orders": "/api/v1/orders",
    "order": "/api/v1/orders/{order_hash}",
    "positions": "/api/v1/positions/{market_address}",
    "user_positions": "/api/v1/users/{address}/positions",
    "user_orders": "/api/v1/users/{address}/orders",
    "user_activity": "/api/v1/users/{address}/activity",
    "user_claimable": "/api/v1/users/{address}/claimable",
    "user_stats": "/api/v1/user-stats",

    # Relayer endpoints
    "ctf_approval": "/api/v1/relayer/ctf-approval",
    "usdc_permit": "/api/v1/relayer/usdc-permit",
    "ctf_redemption": "/api/v1/relayer/ctf-redemption",
    "batch_ctf_redemption": "/api/v1/relayer/batch-ctf-redemption",
}

# WebSocket endpoint
WS_ENDPOINT = "/api/v1/stream"

# EIP-712 domain
EIP712_DOMAIN_NAME = "Turbine"
EIP712_DOMAIN_VERSION = "1"

# EIP-712 Order type
EIP712_ORDER_TYPE = "Order(bytes32 marketId,address trader,uint8 side,uint8 outcome,uint256 price,uint256 size,uint256 nonce,uint256 expiration,address makerFeeRecipient)"

# Bearer token validity window (seconds)
BEARER_TOKEN_VALIDITY = 300  # 5 minutes

# HTTP headers
HEADER_AUTHORIZATION = "Authorization"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_USER_AGENT = "User-Agent"

# User agent string
USER_AGENT = "turbine-py-client/0.1.0"
