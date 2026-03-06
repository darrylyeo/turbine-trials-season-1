"""
Meta-strategy bot: runs all directional strategies and selects the next one based on
prior period profitability. Tracks PnL per strategy and deploys the best performer.
"""

import argparse
import asyncio
import os
from collections import deque
from pathlib import Path

from dotenvx import load_dotenvx

from price_action_bot import (
	AssetState,
	PriceActionBot,
	CHAIN_ID,
	CLAIM_ONLY_MODE,
	DEFAULT_MAX_POSITION_USDC,
	DEFAULT_ORDER_SIZE_USDC,
	PRICE_POLL_SECONDS,
	SUPPORTED_ASSETS,
	TURBINE_HOST,
	get_or_create_api_credentials,
)
from strategies import STRATEGIES, StrategySelector
from turbine_client import TurbineClient

load_dotenvx()

STRATEGY_IDS = list(STRATEGIES.keys())
PRICE_HISTORY_LEN = 30


class MetaStrategyBot(PriceActionBot):
	"""Runs one strategy at a time per market; selects strategy from prior PnL."""

	def __init__(self, *args, dry_run: bool = False, history_path: Path | None = None, **kwargs):
		super().__init__(*args, **kwargs)
		self.dry_run = dry_run
		self.selector = StrategySelector(STRATEGY_IDS, history_path=history_path)
		self.current_strategy_id = STRATEGY_IDS[0]
		self.market_to_strategy: dict[str, str] = {}
		self.price_history: dict[str, deque[float]] = {
			asset: deque(maxlen=PRICE_HISTORY_LEN) for asset in self.assets
		}

	async def calculate_signal(self, state: AssetState, current_price: float) -> tuple[str, float]:
		self.price_history[state.asset].append(current_price)
		context = {
			"client": self.client,
			"price_history": self.price_history,
		}
		fn = STRATEGIES[self.current_strategy_id]
		action, confidence = await fn(state, current_price, context)
		if action != "HOLD":
			print(f"[META] strategy={self.current_strategy_id} | {state.asset} -> {action} (conf: {confidence:.0%})")
		return action, confidence

	async def execute_signal(self, state: AssetState, action: str, confidence: float) -> None:
		if action != "HOLD":
			print(f"[META] strategy={self.current_strategy_id} | {state.asset} executing {action}")
		if self.dry_run and action != "HOLD" and confidence >= 0.6:
			price = self.confidence_to_price(action, confidence)
			shares = self.calculate_shares_from_usdc(self.order_size_usdc, price)
			outcome_str = "YES" if action == "BUY_YES" else "NO"
			print(f"[DRY-RUN] {state.asset} would place {outcome_str} @ {price/10000:.1f}% | ${self.order_size_usdc:.2f} = {shares/1_000_000:.4f} shares")
			return
		await super().execute_signal(state, action, confidence)

	async def switch_to_new_market(self, state: AssetState, new_market_id: str, start_price: int = 0) -> None:
		self.current_strategy_id = self.selector.choose()
		self.market_to_strategy[new_market_id] = self.current_strategy_id
		print(f"[META] strategy={self.current_strategy_id} | {state.asset} selected for new market {new_market_id[:8]}...")
		await super().switch_to_new_market(state, new_market_id, start_price)

	async def claim_resolved_markets(self) -> None:
		retry_delay = 120
		while self.running:
			try:
				all_traded: list[tuple[str, str, AssetState]] = []
				for state in self.asset_states.values():
					for market_id, contract_address in list(state.traded_markets.items()):
						all_traded.append((market_id, contract_address, state))
				if not all_traded:
					await asyncio.sleep(retry_delay)
					continue
				resolved: list[tuple[str, str, AssetState]] = []
				for market_id, contract_address, state in all_traded:
					try:
						resolution = self.client.get_resolution(market_id)
						if resolution and resolution.resolved:
							resolved.append((market_id, contract_address, state))
					except Exception:
						continue
				if not resolved:
					await asyncio.sleep(retry_delay)
					continue
				market_addresses = [addr for _, addr, _ in resolved]
				try:
					result = self.client.batch_claim_winnings(market_addresses)
					tx_hash = result.get("txHash", result.get("tx_hash", "unknown"))
					print(f"💰 Batch claimed {len(resolved)} markets TX: {tx_hash}")
					for market_id, _, state in resolved:
						del state.traded_markets[market_id]
						strategy_id = self.market_to_strategy.pop(market_id, None)
						if strategy_id:
							self.selector.record(strategy_id, 1.0)
				except ValueError as e:
					if "no winning tokens" in str(e).lower():
						for market_id, _, state in resolved:
							del state.traded_markets[market_id]
							strategy_id = self.market_to_strategy.pop(market_id, None)
							if strategy_id:
								self.selector.record(strategy_id, 0.0)
					else:
						print(f"Claim error: {e}")
				except Exception as e:
					print(f"Batch claim error: {e}")
			except Exception as e:
				if "no winning tokens" not in str(e).lower():
					print(f"Claim monitor error: {e}")
			await asyncio.sleep(retry_delay)


async def main():
	parser = argparse.ArgumentParser(
		description="Meta-strategy bot: selects strategy from prior PnL"
	)
	parser.add_argument("-s", "--order-size", type=float, default=DEFAULT_ORDER_SIZE_USDC)
	parser.add_argument("-m", "--max-position", type=float, default=DEFAULT_MAX_POSITION_USDC)
	parser.add_argument(
		"-a", "--assets",
		type=str,
		default=",".join(SUPPORTED_ASSETS),
	)
	parser.add_argument("--history", type=str, default="", help="Path to .strategy_history file")
	parser.add_argument("--dry-run", action="store_true", help="No real orders; log signals only")
	args = parser.parse_args()
	assets = [a.strip().upper() for a in args.assets.split(",")]
	for asset in assets:
		if asset not in SUPPORTED_ASSETS:
			parser.error(f"Unsupported asset '{asset}'. Supported: {', '.join(SUPPORTED_ASSETS)}")
	private_key = os.environ.get("TURBINE_PRIVATE_KEY")
	if not private_key:
		print("Error: Set TURBINE_PRIVATE_KEY in your .env file")
		return
	api_key_id, api_private_key = get_or_create_api_credentials()
	client = TurbineClient(
		host=TURBINE_HOST,
		chain_id=CHAIN_ID,
		private_key=private_key,
		api_key_id=api_key_id,
		api_private_key=api_private_key,
	)
	history_path = Path(args.history).resolve() if args.history else None
	bot = MetaStrategyBot(
		client,
		assets=assets,
		order_size_usdc=args.order_size,
		max_position_usdc=args.max_position,
		dry_run=args.dry_run,
		history_path=history_path,
	)
	scores = bot.selector.summary()
	print(f"\n{'='*60}")
	print("META-STRATEGY BOT" + (" [DRY-RUN — no real orders]" if args.dry_run else ""))
	print(f"{'='*60}")
	print(f"Wallet: {client.address}")
	print(f"Chain: {CHAIN_ID}")
	print(f"Order: ${args.order_size:.2f} | Max pos: ${args.max_position:.2f}")
	print(f"Strategies: {', '.join(STRATEGY_IDS)}")
	print(f"Prior PnL (rolling): {scores}")
	print(f"Next strategy: {bot.selector.choose()}")
	print(f"{'='*60}\n")
	try:
		await bot.run()
	except KeyboardInterrupt:
		pass
	finally:
		print("\nShutting down...")
		bot.running = False
		await bot.cancel_all_orders()
		client.close()
		print("Bot stopped.")


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		pass
