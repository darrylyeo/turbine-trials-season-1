"""
WebSocket client for real-time Turbine market data.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, List, Optional, Set

import websockets
from websockets.asyncio.client import ClientConnection

from turbine_client.constants import WS_ENDPOINT
from turbine_client.exceptions import WebSocketError
from turbine_client.types import (
    OrderBookSnapshot,
    OrderBookUpdate,
    QuickMarketUpdate,
    Trade,
    TradeUpdate,
    WSMessage,
)


class WSStream:
    """WebSocket stream for receiving market data."""

    def __init__(self, connection: ClientConnection) -> None:
        """Initialize the stream.

        Args:
            connection: The WebSocket connection.
        """
        self._connection = connection
        self._subscriptions: Set[str] = set()

    async def subscribe(self, market_id: str) -> None:
        """Subscribe to a market to receive orderbook and trade updates.

        The Turbine WebSocket API uses market-level subscriptions. Once subscribed
        to a market, you will receive ALL updates for that market including:
        - Orderbook updates (type="orderbook")
        - Trade updates (type="trade")
        - Order cancelled updates (type="order_cancelled")

        Args:
            market_id: The market ID to subscribe to (0x... hex string).

        Example:
            await stream.subscribe("0x1234...abcd")
        """
        message = {
            "type": "subscribe",
            "marketId": market_id,
        }

        await self._connection.send(json.dumps(message))

        # Track subscription
        self._subscriptions.add(market_id)

    async def unsubscribe(self, market_id: str) -> None:
        """Unsubscribe from a market.

        Args:
            market_id: The market ID to unsubscribe from.
        """
        message = {
            "type": "unsubscribe",
            "marketId": market_id,
        }

        await self._connection.send(json.dumps(message))

        # Remove subscription
        self._subscriptions.discard(market_id)

    # Convenience aliases for backwards compatibility
    async def subscribe_orderbook(self, market_id: str) -> None:
        """Subscribe to a market (receives orderbook + trade updates).

        Note: The Turbine API subscribes to markets, not channels.
        This is an alias for subscribe() for backwards compatibility.

        Args:
            market_id: The market ID.
        """
        await self.subscribe(market_id)

    async def subscribe_trades(self, market_id: str) -> None:
        """Subscribe to a market (receives orderbook + trade updates).

        Note: The Turbine API subscribes to markets, not channels.
        This is an alias for subscribe() for backwards compatibility.

        Args:
            market_id: The market ID.
        """
        await self.subscribe(market_id)

    def _parse_single_message(self, data: dict) -> WSMessage:
        """Parse a single JSON message dict into a WSMessage."""
        msg_type = data.get("type", "")

        if msg_type == "orderbook":
            return OrderBookUpdate(
                type=msg_type,
                market_id=data.get("marketId"),
                data=data.get("data"),
            )
        elif msg_type == "trade":
            return TradeUpdate(
                type=msg_type,
                market_id=data.get("marketId"),
                data=data.get("data"),
            )
        elif msg_type == "quick_market":
            return QuickMarketUpdate(
                type=msg_type,
                market_id=data.get("marketId"),
                data=data.get("data"),
            )
        else:
            return WSMessage.from_dict(data)

    def _parse_message(self, raw: str) -> List[WSMessage]:
        """Parse a raw WebSocket message (may contain multiple JSON objects).

        Args:
            raw: The raw message string.

        Returns:
            A list of parsed WSMessages.
        """
        messages = []
        # Handle newline-delimited JSON (multiple objects in one message)
        for line in raw.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                messages.append(self._parse_single_message(data))
            except json.JSONDecodeError as e:
                raise WebSocketError(f"Failed to parse message: {e}") from e
        return messages

    async def __aiter__(self) -> AsyncIterator[WSMessage]:
        """Iterate over incoming messages.

        Yields:
            Parsed WebSocket messages.
        """
        try:
            async for raw_message in self._connection:
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode("utf-8")
                for msg in self._parse_message(raw_message):
                    yield msg
        except websockets.exceptions.ConnectionClosed:
            pass

    async def recv(self) -> List[WSMessage]:
        """Receive messages from a single WebSocket frame.

        Returns:
            A list of messages (may contain multiple if server batches them).

        Raises:
            WebSocketError: If the connection is closed.
        """
        try:
            raw = await self._connection.recv()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            return self._parse_message(raw)
        except websockets.exceptions.ConnectionClosed as e:
            raise WebSocketError(f"Connection closed: {e}") from e

    async def close(self) -> None:
        """Close the stream."""
        await self._connection.close()


class TurbineWSClient:
    """WebSocket client for Turbine real-time data."""

    def __init__(
        self,
        host: str,
        reconnect: bool = True,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 60.0,
    ) -> None:
        """Initialize the WebSocket client.

        Args:
            host: The WebSocket host URL (wss://...).
            reconnect: Whether to auto-reconnect on disconnect.
            reconnect_delay: Initial reconnect delay in seconds.
            max_reconnect_delay: Maximum reconnect delay in seconds.
        """
        # Convert http(s) to ws(s) if needed
        if host.startswith("http://"):
            host = "ws://" + host[7:]
        elif host.startswith("https://"):
            host = "wss://" + host[8:]

        self._host = host.rstrip("/")
        self._reconnect = reconnect
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._connection: Optional[ClientConnection] = None

    @property
    def url(self) -> str:
        """Get the WebSocket URL."""
        return f"{self._host}{WS_ENDPOINT}"

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[WSStream]:
        """Connect to the WebSocket server.

        Yields:
            A WSStream for sending/receiving messages.

        Example:
            async with client.connect() as stream:
                await stream.subscribe("0x1234...market_id")
                async for message in stream:
                    if message.type == "trade":
                        print(f"Trade: {message.trade}")
                    elif message.type == "orderbook":
                        print(f"Orderbook update")
        """
        try:
            self._connection = await websockets.connect(self.url)
            stream = WSStream(self._connection)
            yield stream
        finally:
            if self._connection:
                await self._connection.close()
                self._connection = None

    async def connect_with_retry(self) -> WSStream:
        """Connect with automatic reconnection.

        Returns:
            A WSStream for sending/receiving messages.

        Note:
            This method will keep trying to connect indefinitely.
            Use connect() for a single connection attempt.
        """
        delay = self._reconnect_delay

        while True:
            try:
                self._connection = await websockets.connect(self.url)
                return WSStream(self._connection)
            except Exception as e:
                if not self._reconnect:
                    raise WebSocketError(f"Connection failed: {e}") from e

                await asyncio.sleep(delay)
                delay = min(delay * 2, self._max_reconnect_delay)

    async def close(self) -> None:
        """Close the connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
