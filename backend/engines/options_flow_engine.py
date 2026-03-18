"""
Options Flow Engine
Detects unusual options activity — large premiums, volume/OI spikes.

Data source: Yahoo Finance options chains via yfinance (3 nearest expiries).
Falls back to seeded mock data when the request fails.

Signal triggers when:
  option_premium > 500_000  AND  volume / open_interest > 3
"""
import random
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from models.signals import OptionsFlowSignal, SignalDirection
from services.log_service import add_log, SOURCE_REAL, SOURCE_MOCK, SOURCE_ERROR

logger = logging.getLogger(__name__)

_OPTION_EXPIRIES = [7, 14, 21, 30, 45, 60, 90]


def _seed(ticker: str) -> int:
    return sum(ord(c) for c in ticker)


# ── Yahoo Finance options chain ─────────────────────────────────────────────

def _fetch_yahoo_options(ticker: str, price: float) -> Optional[List[OptionsFlowSignal]]:
    """
    Fetch options flow from Yahoo Finance (3 nearest expiry dates).
    Returns None on failure so caller can fall back to mock.
    """
    try:
        import yfinance as yf
        import pandas as pd

        t = yf.Ticker(ticker)
        expiries = t.options          # tuple of date strings
        if not expiries:
            return None

        signals: List[OptionsFlowSignal] = []
        # Scan up to the 3 nearest expiry dates
        for expiry in expiries[:3]:
            try:
                chain = t.option_chain(expiry)
            except Exception:
                continue

            for option_type, df in [("call", chain.calls), ("put", chain.puts)]:
                if df is None or df.empty:
                    continue

                for _, row in df.iterrows():
                    try:
                        volume = int(row.get("volume") or 0)
                        if volume == 0:
                            continue

                        open_interest = int(row.get("openInterest") or 0)
                        last_price = float(row.get("lastPrice") or 0)
                        strike = float(row.get("strike") or 0)
                        implied_vol = float(row.get("impliedVolatility") or 0)

                        total_premium = last_price * volume * 100
                        vol_oi_ratio = round(volume / max(open_interest, 1), 3)

                        # Derive simple Greeks approximations if not supplied
                        gamma = round(implied_vol * 0.02, 5)
                        delta = 0.5 if option_type == "call" else -0.5

                        direction = (
                            SignalDirection.BULLISH if option_type == "call"
                            else SignalDirection.BEARISH
                        )

                        score = 0.0
                        if total_premium > 500_000 and vol_oi_ratio > 3:
                            score = (
                                min(50.0, total_premium / 5_000_000 * 50)
                                + min(50.0, vol_oi_ratio / 10 * 50)
                            )

                        signals.append(OptionsFlowSignal(
                            ticker=ticker,
                            premium=round(total_premium, 2),
                            strike=strike,
                            expiration=expiry,
                            direction=direction,
                            volume=volume,
                            open_interest=open_interest,
                            volume_oi_ratio=vol_oi_ratio,
                            option_type=option_type,
                            timestamp=datetime.utcnow(),
                            score=round(score, 2),
                        ))
                    except Exception:
                        continue

        if not signals:
            return None

        add_log("options", ticker, SOURCE_REAL, f"Yahoo Finance — {len(signals)} contracts across {min(len(expiries),3)} expiries")
        return sorted(signals, key=lambda s: s.premium, reverse=True)[:20]

    except Exception as exc:
        add_log("options", ticker, SOURCE_ERROR, str(exc)[:120])
        logger.warning("Yahoo options fetch failed for %s: %s", ticker, exc)
        return None


# ── Mock fallback ───────────────────────────────────────────────────────────

def _mock_options_flow(ticker: str, price: float) -> List[OptionsFlowSignal]:
    rng = random.Random(_seed(ticker) + int(datetime.utcnow().hour))
    signals: List[OptionsFlowSignal] = []
    num_contracts = rng.randint(3, 12)

    for _ in range(num_contracts):
        option_type = rng.choice(["call", "call", "call", "put"])
        offset = rng.uniform(-0.15, 0.20) if option_type == "call" else rng.uniform(-0.20, 0.05)
        strike = round(price * (1 + offset) / 5) * 5

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

    return sorted(signals, key=lambda s: s.premium, reverse=True)


# ── Public API ──────────────────────────────────────────────────────────────

def get_options_flow(ticker: str, price: float) -> List[OptionsFlowSignal]:
    """Return options flow signals. Real data when available, mock as fallback."""
    real = _fetch_yahoo_options(ticker, price)
    if real is not None:
        return real
    add_log("options", ticker, SOURCE_MOCK, "Yahoo Finance unavailable — seeded mock")
    return _mock_options_flow(ticker, price)


def compute_options_flow_score(signals: List[OptionsFlowSignal]) -> float:
    """Aggregate options flow into a 0–100 score."""
    if not signals:
        return 0.0
    triggered = [s for s in signals if s.premium > 500_000 and s.volume_oi_ratio > 3]
    if not triggered:
        best = max(signals, key=lambda s: s.premium)
        return min(25.0, best.premium / 500_000 * 25)
    score = sum(
        min(50.0, s.premium / 5_000_000 * 50) + min(50.0, s.volume_oi_ratio / 10 * 50)
        for s in triggered[:3]
    ) / 3
    return round(min(100.0, score), 2)
