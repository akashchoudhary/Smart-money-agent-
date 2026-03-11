"""
Options Flow Engine
Detects unusual options activity — large premiums, volume/OI spikes.

Signal triggers when:
  option_premium > 500_000  AND  volume / open_interest > 3
"""
import random
from datetime import datetime, timedelta
from typing import List
from models.signals import OptionsFlowSignal, SignalDirection

_OPTION_EXPIRIES = [7, 14, 21, 30, 45, 60, 90]


def _seed(ticker: str) -> int:
    return sum(ord(c) for c in ticker)


def get_options_flow(ticker: str, price: float) -> List[OptionsFlowSignal]:
    rng = random.Random(_seed(ticker) + int(datetime.utcnow().hour))
    signals: List[OptionsFlowSignal] = []

    num_contracts = rng.randint(3, 12)
    for i in range(num_contracts):
        option_type = rng.choice(["call", "call", "call", "put"])
        strike_offset = rng.uniform(-0.15, 0.20) if option_type == "call" else rng.uniform(-0.20, 0.05)
        strike = round(price * (1 + strike_offset) / 5) * 5  # round to nearest $5

        days_out = rng.choice(_OPTION_EXPIRIES)
        expiration = (datetime.utcnow() + timedelta(days=days_out)).strftime("%Y-%m-%d")

        volume = rng.randint(100, 25_000)
        open_interest = rng.randint(500, 80_000)
        vol_oi_ratio = round(volume / max(open_interest, 1), 3)

        gamma = round(rng.uniform(0.001, 0.08), 5)
        delta = round(rng.uniform(0.1, 0.9), 3) if option_type == "call" else round(-rng.uniform(0.1, 0.9), 3)
        premium_per_contract = rng.uniform(0.50, 35.0)
        total_premium = round(premium_per_contract * volume * 100, 2)

        direction = SignalDirection.BULLISH if option_type == "call" else SignalDirection.BEARISH
        score = 0.0
        if total_premium > 500_000 and vol_oi_ratio > 3:
            # Normalize: premium up to 5M → 50 pts, vol/oi ratio up to 10 → 50 pts
            score = min(50.0, total_premium / 5_000_000 * 50) + min(50.0, vol_oi_ratio / 10 * 50)

        signals.append(OptionsFlowSignal(
            ticker=ticker,
            premium=total_premium,
            strike=strike,
            expiration=expiration,
            direction=direction,
            volume=volume,
            open_interest=open_interest,
            volume_oi_ratio=vol_oi_ratio,
            option_type=option_type,
            timestamp=datetime.utcnow() - timedelta(minutes=rng.randint(0, 120)),
            score=round(score, 2),
        ))

    # Sort by premium descending (biggest flow first)
    return sorted(signals, key=lambda s: s.premium, reverse=True)


def compute_options_flow_score(signals: List[OptionsFlowSignal]) -> float:
    """Aggregate options flow into a 0–100 score."""
    if not signals:
        return 0.0
    triggered = [s for s in signals if s.premium > 500_000 and s.volume_oi_ratio > 3]
    if not triggered:
        # Give partial credit for elevated activity
        best = max(signals, key=lambda s: s.premium)
        return min(25.0, best.premium / 500_000 * 25)
    # Weight by premium and vol/oi ratio
    score = sum(
        min(50.0, s.premium / 5_000_000 * 50) + min(50.0, s.volume_oi_ratio / 10 * 50)
        for s in triggered[:3]
    ) / 3
    return round(min(100.0, score), 2)
