"""
Gamma Exposure Engine

GammaExposure = OptionGamma × OpenInterest × ContractSize × SpotPrice

Positive GEX → dealers are long gamma → volatility suppression
Negative GEX → dealers are short gamma → volatility expansion

dealer_delta = call_delta - put_delta
Large positive dealer_delta → bullish pressure
"""
import random
import math
from datetime import datetime, timedelta
from typing import List
from models.signals import GammaExposureSignal

CONTRACT_SIZE = 100


def _seed(ticker: str) -> int:
    return sum((ord(c) ** 2) for c in ticker)


def get_gamma_exposure(ticker: str, price: float) -> GammaExposureSignal:
    rng = random.Random(_seed(ticker) + int(datetime.utcnow().hour))

    # Simulate call-side and put-side gamma
    call_oi = rng.randint(10_000, 500_000)
    put_oi = rng.randint(10_000, 400_000)
    call_gamma = rng.uniform(0.001, 0.06)
    put_gamma = rng.uniform(0.001, 0.05)
    call_delta = rng.uniform(0.1, 0.85)
    put_delta = rng.uniform(0.1, 0.85)

    call_gex = call_gamma * call_oi * CONTRACT_SIZE * price
    put_gex = -put_gamma * put_oi * CONTRACT_SIZE * price  # dealers short puts → negative contribution
    net_gex = call_gex + put_gex

    dealer_delta = (call_delta * call_oi) - (put_delta * put_oi)

    # Gamma flip level: price where GEX crosses zero (simplified estimate)
    gamma_flip = round(price * rng.uniform(0.92, 1.08), 2)

    interpretation = "volatility suppression" if net_gex > 0 else "volatility expansion"

    # Score: use absolute GEX magnitude + dealer delta signal
    gex_score = min(50.0, abs(net_gex) / 500_000_000 * 50)
    delta_score = min(50.0, abs(dealer_delta) / 200_000 * 50) if dealer_delta > 0 else 0.0
    score = round(gex_score + delta_score, 2)

    return GammaExposureSignal(
        ticker=ticker,
        gamma_exposure=round(net_gex, 2),
        spot_price=price,
        dealer_delta=round(dealer_delta, 2),
        gamma_flip_level=gamma_flip,
        interpretation=interpretation,
        timestamp=datetime.utcnow(),
        score=score,
    )


def get_gamma_history(ticker: str, price: float, days: int = 30) -> List[GammaExposureSignal]:
    history: List[GammaExposureSignal] = []
    for d in range(days):
        rng = random.Random(_seed(ticker) + d)
        call_oi = rng.randint(10_000, 500_000)
        put_oi = rng.randint(10_000, 400_000)
        call_gamma = rng.uniform(0.001, 0.06)
        put_gamma = rng.uniform(0.001, 0.05)
        call_delta = rng.uniform(0.1, 0.85)
        put_delta = rng.uniform(0.1, 0.85)

        call_gex = call_gamma * call_oi * CONTRACT_SIZE * price
        put_gex = -put_gamma * put_oi * CONTRACT_SIZE * price
        net_gex = call_gex + put_gex
        dealer_delta = (call_delta * call_oi) - (put_delta * put_oi)
        interpretation = "volatility suppression" if net_gex > 0 else "volatility expansion"
        gamma_flip = round(price * rng.uniform(0.92, 1.08), 2)

        gex_score = min(50.0, abs(net_gex) / 500_000_000 * 50)
        delta_score = min(50.0, abs(dealer_delta) / 200_000 * 50) if dealer_delta > 0 else 0.0
        score = round(gex_score + delta_score, 2)

        history.append(GammaExposureSignal(
            ticker=ticker,
            gamma_exposure=round(net_gex, 2),
            spot_price=price,
            dealer_delta=round(dealer_delta, 2),
            gamma_flip_level=gamma_flip,
            interpretation=interpretation,
            timestamp=datetime.utcnow() - timedelta(days=days - d),
            score=score,
        ))
    return history


def compute_gamma_score(signal: GammaExposureSignal) -> float:
    return signal.score
