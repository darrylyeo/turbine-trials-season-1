"""Selects which strategy to run next based on prior period PnL."""

from pathlib import Path

DEFAULT_HISTORY_PATH = Path(__file__).resolve().parent.parent / ".strategy_history"
LOOKBACK_MARKETS = 20


class StrategySelector:
	"""Tracks per-strategy PnL and returns the best-performing strategy for the next period."""

	def __init__(self, strategy_ids: list[str], history_path: Path | None = None):
		self.strategy_ids = strategy_ids
		self.history_path = history_path or DEFAULT_HISTORY_PATH
		self._recent: list[tuple[str, float]] = []
		self._load()

	def _load(self) -> None:
		if not self.history_path.exists():
			return
		try:
			lines = self.history_path.read_text().strip().splitlines()
			for line in lines:
				parts = line.split(",", 1)
				if len(parts) == 2:
					try:
						self._recent.append((parts[0].strip(), float(parts[1])))
					except ValueError:
						pass
			self._recent = self._recent[-LOOKBACK_MARKETS:]
		except Exception:
			pass

	def _save(self) -> None:
		try:
			self.history_path.parent.mkdir(parents=True, exist_ok=True)
			self.history_path.write_text(
				"\n".join(f"{s},{pnl}" for s, pnl in self._recent[-LOOKBACK_MARKETS:]) + "\n"
			)
		except Exception:
			pass

	def record(self, strategy_id: str, pnl: float) -> None:
		self._recent.append((strategy_id, pnl))
		if len(self._recent) > LOOKBACK_MARKETS:
			self._recent = self._recent[-LOOKBACK_MARKETS:]
		self._save()

	def choose(self) -> str:
		if not self._recent:
			return self.strategy_ids[0]
		scores: dict[str, float] = {s: 0.0 for s in self.strategy_ids}
		for strategy_id, pnl in self._recent:
			if strategy_id in scores:
				scores[strategy_id] += pnl
		best = max(self.strategy_ids, key=lambda s: scores[s])
		return best

	def summary(self) -> dict[str, float]:
		scores: dict[str, float] = {s: 0.0 for s in self.strategy_ids}
		for strategy_id, pnl in self._recent:
			if strategy_id in scores:
				scores[strategy_id] += pnl
		return scores
