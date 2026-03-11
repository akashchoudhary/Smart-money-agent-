"""
Market Data Engine
Generates/fetches price, volume, market cap data for tracked tickers.
Mock implementation — replace fetch_ticker() with real broker API calls.
"""
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from models.signals import MarketData, PricePoint

UNIVERSE = [
    "NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "AMD",
    "NFLX", "SPY", "QQQ", "PLTR", "RIVN", "SOFI", "GME", "MARA",
    "COIN", "HOOD", "RBLX", "SNOW", "DDOG", "PYPL", "SQ", "UBER",
    "ABNB", "DIS", "BA", "JPM", "GS", "MS"
]

# Seed data so results are deterministic within a session
_BASE_PRICES: Dict[str, float] = {
    "NVDA": 875.0, "AAPL": 182.0, "MSFT": 415.0, "TSLA": 248.0,
    "AMZN": 192.0, "GOOGL": 167.0, "META": 498.0, "AMD": 175.0,
    "NFLX": 623.0, "SPY": 521.0, "QQQ": 448.0, "PLTR": 22.0,
    "RIVN": 11.0, "SOFI": 7.5, "GME": 16.0, "MARA": 18.0,
    "COIN": 225.0, "HOOD": 18.0, "RBLX": 38.0, "SNOW": 152.0,
    "DDOG": 125.0, "PYPL": 63.0, "SQ": 72.0, "UBER": 78.0,
    "ABNB": 163.0, "DIS": 112.0, "BA": 195.0, "JPM": 198.0,
    "GS": 432.0, "MS": 102.0,
}

_BASE_MCAP: Dict[str, float] = {
    "NVDA": 2_150_000_000_000, "AAPL": 2_800_000_000_000,
    "MSFT": 3_080_000_000_000, "TSLA": 790_000_000_000,
    "AMZN": 1_980_000_000_000, "GOOGL": 2_100_000_000_000,
    "META": 1_270_000_000_000, "AMD": 283_000_000_000,
    "NFLX": 272_000_000_000, "SPY": 490_000_000_000,
    "QQQ": 245_000_000_000, "PLTR": 46_000_000_000,
    "RIVN": 10_500_000_000, "SOFI": 7_200_000_000,
    "GME": 4_900_000_000, "MARA": 3_800_000_000,
    "COIN": 55_000_000_000, "HOOD": 15_200_000_000,
    "RBLX": 24_000_000_000, "SNOW": 51_000_000_000,
    "DDOG": 40_000_000_000, "PYPL": 67_000_000_000,
    "SQ": 43_000_000_000, "UBER": 162_000_000_000,
    "ABNB": 104_000_000_000, "DIS": 205_000_000_000,
    "BA": 114_000_000_000, "JPM": 568_000_000_000,
    "GS": 141_000_000_000, "MS": 170_000_000_000,
}


def _seed(ticker: str) -> int:
    return sum(ord(c) for c in ticker)


def get_market_data(ticker: str) -> MarketData:
    rng = random.Random(_seed(ticker) + int(datetime.utcnow().hour))
    base_price = _BASE_PRICES.get(ticker, 50.0)
    noise = rng.uniform(-0.03, 0.05)
    price = round(base_price * (1 + noise), 2)
    change_pct = round(rng.uniform(-4.5, 6.5), 2)

    avg_vol = int(rng.uniform(5_000_000, 80_000_000))
    vol_multiplier = rng.choice([1.0, 1.2, 1.5, 2.1, 3.4, 4.2])
    volume = int(avg_vol * vol_multiplier)
    volume_ratio = round(volume / avg_vol, 2)

    high_52w = round(price * rng.uniform(1.05, 1.6), 2)
    low_52w = round(price * rng.uniform(0.45, 0.92), 2)
    short_interest = round(rng.uniform(0.01, 0.35), 4)

    return MarketData(
        ticker=ticker,
        price=price,
        change_pct=change_pct,
        volume=volume,
        avg_volume_30d=avg_vol,
        volume_ratio=volume_ratio,
        market_cap=_BASE_MCAP.get(ticker, 10_000_000_000),
        short_interest=short_interest,
        high_52w=high_52w,
        low_52w=low_52w,
    )


def get_price_history(ticker: str, days: int = 90) -> List[PricePoint]:
    rng = random.Random(_seed(ticker))
    base_price = _BASE_PRICES.get(ticker, 50.0)
    points: List[PricePoint] = []
    price = base_price * rng.uniform(0.75, 0.95)

    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - i)
        daily_return = rng.gauss(0.001, 0.022)
        price = max(price * (1 + daily_return), 1.0)

        high = price * rng.uniform(1.002, 1.025)
        low = price * rng.uniform(0.975, 0.998)
        open_p = price * rng.uniform(0.995, 1.005)
        volume = int(rng.uniform(3_000_000, 60_000_000))

        points.append(PricePoint(
            time=date.strftime("%Y-%m-%d"),
            open=round(open_p, 2),
            high=round(high, 2),
            low=round(low, 2),
            close=round(price, 2),
            volume=volume,
        ))

    return points


def compute_volume_spike_score(market_data: MarketData) -> float:
    """Normalize volume ratio to 0–100 score."""
    ratio = market_data.volume_ratio
    if ratio < 1.0:
        return 0.0
    if ratio >= 5.0:
        return 100.0
    # Linear between 1x and 5x → 0–100
    return min(100.0, (ratio - 1.0) / 4.0 * 100.0)


def get_universe() -> List[str]:
    return UNIVERSE
