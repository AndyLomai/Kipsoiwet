from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from .martingale import Side


@dataclass(slots=True)
class MarketSnapshot:
    market_slug: str
    up_price: float
    down_price: float
    asof: datetime


class PolymarketClient:
    """
    Lightweight market data client.

    Trading execution is intentionally disabled by default. The bot computes and reports
    stakes in real time, and can be extended with authenticated execution later.
    """

    def __init__(self, market_slug: str, timeout_s: float = 5.0) -> None:
        self.market_slug = market_slug
        self.timeout_s = timeout_s

    async def get_snapshot(self) -> MarketSnapshot:
        # Public endpoint used only for top-of-book indicative prices.
        url = "https://gamma-api.polymarket.com/events"
        params = {"slug": self.market_slug}

        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        if not payload:
            raise ValueError(f"No event returned for slug={self.market_slug}")

        markets = payload[0].get("markets", [])
        if len(markets) < 2:
            raise ValueError("Expected at least two market outcomes")

        # Heuristic: pick first two outcomes as UP and DOWN for the chosen event.
        up_price = float(markets[0].get("lastTradePrice") or markets[0].get("bestAsk") or 0.0)
        down_price = float(markets[1].get("lastTradePrice") or markets[1].get("bestAsk") or 0.0)

        if up_price <= 0 or down_price <= 0:
            raise ValueError("Could not infer valid prices from market snapshot")

        return MarketSnapshot(
            market_slug=self.market_slug,
            up_price=up_price,
            down_price=down_price,
            asof=datetime.now(tz=timezone.utc),
        )

    @staticmethod
    def side_price(snapshot: MarketSnapshot, side: Side) -> float:
        return snapshot.up_price if side == Side.UP else snapshot.down_price
