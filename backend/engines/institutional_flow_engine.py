"""
Institutional Flow Engine
Tracks block trades (>10,000 shares) and ETF fund flows.
"""
import random
from datetime import datetime, timedelta
from typing import List
from models.signals import InstitutionalFlowSignal

_ETF_MAP = {
    "NVDA": ["SMH", "SOXX", "QQQ"], "AAPL": ["QQQ", "SPY", "XLK"],
    "MSFT": ["QQQ", "SPY", "XLK"], "TSLA": ["ARKK", "QQQ", "SPY"],
    "AMD": ["SMH", "SOXX", "QQQ"], "AMZN": ["QQQ", "SPY", "XLC"],
    "META": ["QQQ", "SPY", "XLC"], "GOOGL": ["QQQ", "SPY", "XLC"],
}


def _seed(ticker: str) -> int:
    return sum(ord(c) + i * 7 for i, c in enumerate(ticker))


def get_institutional_flow(ticker: str, price: float) -> InstitutionalFlowSignal:
    rng = random.Random(_seed(ticker) + int(datetime.utcnow().hour))

    # Block trade simulation
    num_blocks = rng.randint(2, 20)
    block_trade_volume = sum(rng.randint(10_000, 500_000) * price for _ in range(num_blocks))

    # ETF flow simulation
    etf_inflow = rng.uniform(1_000_000, 80_000_000)
    etf_outflow = etf_inflow * rng.uniform(0.2, 0.95)
    net_etf_flow = etf_inflow - etf_outflow
    large_buyer_count = rng.randint(0, 15)

    score = min(100.0, (block_trade_volume / 500_000_000 * 50) + (net_etf_flow / 100_000_000 * 50))

    return InstitutionalFlowSignal(
        ticker=ticker,
        block_trade_volume=round(block_trade_volume, 0),
        etf_inflow=round(etf_inflow, 0),
        etf_outflow=round(etf_outflow, 0),
        net_etf_flow=round(net_etf_flow, 0),
        large_buyer_count=large_buyer_count,
        timestamp=datetime.utcnow(),
        score=round(score, 2),
    )


def compute_institutional_score(signal: InstitutionalFlowSignal) -> float:
    return signal.score
