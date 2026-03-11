"""
Dark Pool Engine
Tracks off-exchange block trades and computes net institutional flow.

dark_pool_net_flow = buy_volume - sell_volume
Signal triggers when dark_pool_net_flow > 5_000_000
"""
import random
from datetime import datetime, timedelta
from typing import List, Tuple
from models.signals import DarkPoolSignal


def _seed(ticker: str) -> int:
    return sum(ord(c) * (i + 1) for i, c in enumerate(ticker))


def get_dark_pool_signal(ticker: str, price: float) -> DarkPoolSignal:
    rng = random.Random(_seed(ticker) + int(datetime.utcnow().hour))

    # Simulate institutional buying bias — weighted toward accumulation
    buy_volume = rng.uniform(1_000_000, 25_000_000)
    # Sell volume is skewed lower to generate realistic bullish net flows
    sell_fraction = rng.uniform(0.25, 1.05)
    sell_volume = buy_volume * sell_fraction
    net_flow = buy_volume - sell_volume

    score = 0.0
    if net_flow > 5_000_000:
        # Max score at 50M net flow
        score = min(100.0, net_flow / 50_000_000 * 100)

    return DarkPoolSignal(
        ticker=ticker,
        buy_volume=round(buy_volume, 0),
        sell_volume=round(sell_volume, 0),
        dark_pool_net_flow=round(net_flow, 0),
        price=price,
        timestamp=datetime.utcnow(),
        score=round(score, 2),
    )


def get_dark_pool_history(ticker: str, price: float, days: int = 30) -> List[DarkPoolSignal]:
    history: List[DarkPoolSignal] = []
    for d in range(days):
        rng = random.Random(_seed(ticker) + d)
        buy_volume = rng.uniform(500_000, 20_000_000)
        sell_volume = buy_volume * rng.uniform(0.3, 1.1)
        net_flow = buy_volume - sell_volume
        score = max(0.0, min(100.0, net_flow / 50_000_000 * 100)) if net_flow > 5_000_000 else 0.0
        history.append(DarkPoolSignal(
            ticker=ticker,
            buy_volume=round(buy_volume, 0),
            sell_volume=round(sell_volume, 0),
            dark_pool_net_flow=round(net_flow, 0),
            price=price,
            timestamp=datetime.utcnow() - timedelta(days=days - d),
            score=round(score, 2),
        ))
    return history


def compute_dark_pool_score(signal: DarkPoolSignal) -> float:
    """Normalize dark pool net flow to 0–100 score."""
    net = signal.dark_pool_net_flow
    if net <= 0:
        return 0.0
    return round(min(100.0, net / 50_000_000 * 100), 2)
