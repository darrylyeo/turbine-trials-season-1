"""Directional strategy signal functions. Each returns (action, confidence)."""

# Shared constants (mirror price_action_bot)
PRICE_THRESHOLD_BPS = 5
MIN_CONFIDENCE = 0.6
MAX_CONFIDENCE = 0.9
MOMENTUM_LOOKBACK = 30
MOMENTUM_THRESHOLD = 0.65
MEAN_REVERSION_WARMUP = 5
MEAN_REVERSION_THRESHOLD_PCT = 0.15
PROB_EDGE_THRESHOLD_PCT = 2.0


async def price_action_signal(state, current_price: float, context) -> tuple[str, float]:
	"""Price vs strike: above → BUY_YES, below → BUY_NO. Confidence scales with distance."""
	if current_price <= 0:
		return "HOLD", 0.0
	strike_usd = state.strike_price / 1e6
	if strike_usd <= 0:
		return "HOLD", 0.0
	price_diff_pct = ((current_price - strike_usd) / strike_usd) * 100
	threshold_pct = PRICE_THRESHOLD_BPS / 100
	if abs(price_diff_pct) < threshold_pct:
		return "HOLD", 0.0
	raw_confidence = min(abs(price_diff_pct) / 2, MAX_CONFIDENCE)
	confidence = max(raw_confidence, MIN_CONFIDENCE) if abs(price_diff_pct) >= threshold_pct else 0.0
	if price_diff_pct > 0:
		return "BUY_YES", confidence
	return "BUY_NO", confidence


async def momentum_signal(state, current_price: float, context) -> tuple[str, float]:
	"""Follow recent trade flow: buy_ratio > threshold → BUY_YES, < (1-threshold) → BUY_NO."""
	client = context["client"]
	try:
		trades = client.get_trades(market_id=state.market_id, limit=MOMENTUM_LOOKBACK)
	except Exception:
		return "HOLD", 0.0
	if not trades:
		return "HOLD", 0.0
	buys_yes = sum(1 for t in trades if t.outcome == 0)
	buys_no = sum(1 for t in trades if t.outcome == 1)
	total = buys_yes + buys_no
	if total == 0:
		return "HOLD", 0.0
	buy_yes_ratio = buys_yes / total
	if buy_yes_ratio >= MOMENTUM_THRESHOLD:
		return "BUY_YES", MIN_CONFIDENCE + (buy_yes_ratio - MOMENTUM_THRESHOLD) / (1 - MOMENTUM_THRESHOLD) * (MAX_CONFIDENCE - MIN_CONFIDENCE)
	if buy_yes_ratio <= (1 - MOMENTUM_THRESHOLD):
		return "BUY_NO", MIN_CONFIDENCE + ((1 - MOMENTUM_THRESHOLD) - buy_yes_ratio) / (1 - MOMENTUM_THRESHOLD) * (MAX_CONFIDENCE - MIN_CONFIDENCE)
	return "HOLD", 0.0


async def mean_reversion_signal(state, current_price: float, context) -> tuple[str, float]:
	"""Fade moves: price > ma + thresh → BUY_NO, price < ma - thresh → BUY_YES."""
	price_history = context.get("price_history", {}).get(state.asset)
	if not price_history or len(price_history) < MEAN_REVERSION_WARMUP:
		return "HOLD", 0.0
	avg = sum(price_history) / len(price_history)
	diff_pct = ((current_price - avg) / avg) * 100 if avg else 0
	if diff_pct >= MEAN_REVERSION_THRESHOLD_PCT:
		confidence = min(MIN_CONFIDENCE + abs(diff_pct) / 2 * 0.01, MAX_CONFIDENCE)
		return "BUY_NO", confidence
	if diff_pct <= -MEAN_REVERSION_THRESHOLD_PCT:
		confidence = min(MIN_CONFIDENCE + abs(diff_pct) / 2 * 0.01, MAX_CONFIDENCE)
		return "BUY_YES", confidence
	return "HOLD", 0.0


async def probability_weighted_signal(state, current_price: float, context) -> tuple[str, float]:
	"""Fade extremes: price far above strike → BUY_NO (overconfident YES), far below → BUY_YES."""
	if current_price <= 0:
		return "HOLD", 0.0
	strike_usd = state.strike_price / 1e6
	if strike_usd <= 0:
		return "HOLD", 0.0
	diff_pct = ((current_price - strike_usd) / strike_usd) * 100
	if diff_pct >= PROB_EDGE_THRESHOLD_PCT:
		confidence = min(MIN_CONFIDENCE + (diff_pct - PROB_EDGE_THRESHOLD_PCT) / 2, MAX_CONFIDENCE)
		return "BUY_NO", confidence
	if diff_pct <= -PROB_EDGE_THRESHOLD_PCT:
		confidence = min(MIN_CONFIDENCE + (abs(diff_pct) - PROB_EDGE_THRESHOLD_PCT) / 2, MAX_CONFIDENCE)
		return "BUY_YES", confidence
	return "HOLD", 0.0


STRATEGIES = {
	"price_action": price_action_signal,
	"momentum": momentum_signal,
	"mean_reversion": mean_reversion_signal,
	"probability_weighted": probability_weighted_signal,
}
