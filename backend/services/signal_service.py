"""
Signal Service
Orchestrates all engines, computes the Master Score, and caches results.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

import redis.asyncio as aioredis

from config import get_settings
from engines.market_data_engine import (
    get_market_data, get_price_history, compute_volume_spike_score, get_universe
)
from engines.options_flow_engine import get_options_flow, compute_options_flow_score
from engines.dark_pool_engine import get_dark_pool_signal, get_dark_pool_history, compute_dark_pool_score
from engines.gamma_exposure_engine import get_gamma_exposure, get_gamma_history, compute_gamma_score
from engines.insider_engine import get_insider_trades, compute_insider_score
from engines.institutional_flow_engine import get_institutional_flow, compute_institutional_score
from engines.ai_signal_engine import get_ai_signal
from engines.alert_engine import check_and_fire
from models.signals import (
    MasterSignal, SignalStrength, SignalDirection, SignalResponse,
    StockDetailResponse
)

logger = logging.getLogger(__name__)
settings = get_settings()

# -------------------------------------------------------------------
# Master Score weights (must sum to 1.0)
# -------------------------------------------------------------------
WEIGHTS = {
    "options_flow":     0.20,
    "gamma_exposure":   0.20,
    "dark_pool":        0.15,
    "volume_spike":     0.15,
    "insider_buying":   0.10,
    "institutional":    0.10,
    "ai_score":         0.10,
}


def _score_to_strength(score: float) -> SignalStrength:
    if score >= 85:
        return SignalStrength.EXPLOSIVE
    if score >= 70:
        return SignalStrength.STRONG_POSITIONING
    if score >= 40:
        return SignalStrength.ACCUMULATION
    return SignalStrength.WEAK


def _score_to_direction(
    options_score: float,
    dark_pool_score: float,
    insider_score: float,
) -> SignalDirection:
    bull = options_score + dark_pool_score + insider_score
    if bull > 120:
        return SignalDirection.BULLISH
    if bull < 40:
        return SignalDirection.BEARISH
    return SignalDirection.NEUTRAL


def _redis_client() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def compute_master_signal(ticker: str) -> MasterSignal:
    """Synchronous computation — wraps all engines."""
    mkt = get_market_data(ticker)

    options_signals = get_options_flow(ticker, mkt.price)
    dark_pool = get_dark_pool_signal(ticker, mkt.price)
    gamma = get_gamma_exposure(ticker, mkt.price)
    insider_trades = get_insider_trades(ticker, mkt.price)
    institutional = get_institutional_flow(ticker, mkt.price)

    # Sub-scores (0–100)
    options_score = compute_options_flow_score(options_signals)
    dp_score = compute_dark_pool_score(dark_pool)
    gamma_score = compute_gamma_score(gamma)
    vol_score = compute_volume_spike_score(mkt)
    insider_score = compute_insider_score(insider_trades)
    inst_score = compute_institutional_score(institutional)

    # AI score
    insider_flag = 1 if insider_score > 0 else 0
    ai_sig = get_ai_signal(
        ticker=ticker,
        options_flow_score=options_score,
        dark_pool_net_flow=dark_pool.dark_pool_net_flow,
        gamma_exposure=gamma.gamma_exposure,
        short_interest=mkt.short_interest,
        volume_ratio=mkt.volume_ratio,
        insider_buying_flag=insider_flag,
        price_source_divergence=mkt.price_source_divergence,
    )
    ai_score = ai_sig.breakout_probability * 100

    # Weighted master score
    master_score = round(
        options_score  * WEIGHTS["options_flow"] +
        gamma_score    * WEIGHTS["gamma_exposure"] +
        dp_score       * WEIGHTS["dark_pool"] +
        vol_score      * WEIGHTS["volume_spike"] +
        insider_score  * WEIGHTS["insider_buying"] +
        inst_score     * WEIGHTS["institutional"] +
        ai_score       * WEIGHTS["ai_score"],
        2,
    )

    direction = _score_to_direction(options_score, dp_score, insider_score)

    return MasterSignal(
        ticker=ticker,
        master_score=master_score,
        signal_strength=_score_to_strength(master_score),
        direction=direction,
        breakout_probability=ai_sig.breakout_probability,
        options_flow_score=options_score,
        gamma_exposure_score=gamma_score,
        dark_pool_score=dp_score,
        volume_spike_score=vol_score,
        insider_buying_score=insider_score,
        institutional_flow_score=inst_score,
        ai_score=ai_score,
        market_data=mkt,
        top_options_flow=options_signals[0] if options_signals else None,
        dark_pool=dark_pool,
        gamma=gamma,
        insider_trades=insider_trades[:5],
        institutional=institutional,
        timestamp=datetime.utcnow(),
    )


async def get_all_signals(use_cache: bool = True) -> List[SignalResponse]:
    cache_key = "all_signals"
    if use_cache:
        try:
            r = _redis_client()
            cached = await r.get(cache_key)
            await r.aclose()
            if cached:
                data = json.loads(cached)
                return [SignalResponse(**item) for item in data]
        except Exception as e:
            logger.warning("Redis read failed: %s", e)

    tickers = get_universe()
    # Run all tickers concurrently in a thread pool
    loop = asyncio.get_event_loop()
    signals_raw = await asyncio.gather(
        *[loop.run_in_executor(None, compute_master_signal, t) for t in tickers]
    )

    # Fire alerts asynchronously for high-score signals
    await asyncio.gather(
        *[check_and_fire(s) for s in signals_raw],
        return_exceptions=True,
    )

    responses = [
        SignalResponse(
            ticker=s.ticker,
            score=s.master_score,
            breakout_probability=s.breakout_probability,
            dark_pool_flow=s.dark_pool.dark_pool_net_flow if s.dark_pool else 0,
            signal=s.direction.value,
            options_flow_score=s.options_flow_score,
            gamma_score=s.gamma_exposure_score,
            volume_spike_score=s.volume_spike_score,
            insider_score=s.insider_buying_score,
            institutional_score=s.institutional_flow_score,
            price=s.market_data.price,
            change_pct=s.market_data.change_pct,
            market_cap=s.market_data.market_cap,
            price_divergence_flag=s.market_data.price_divergence_flag,
            price_source_divergence=s.market_data.price_source_divergence,
            data_sources=s.market_data.data_sources,
        )
        for s in signals_raw
    ]

    # Sort by master score descending
    responses.sort(key=lambda r: r.score, reverse=True)

    if use_cache:
        try:
            r = _redis_client()
            await r.setex(cache_key, settings.cache_ttl_seconds, json.dumps([r_.model_dump() for r_ in responses], default=str))
            await r.aclose()
        except Exception as e:
            logger.warning("Redis write failed: %s", e)

    return responses


async def get_stock_detail(ticker: str) -> StockDetailResponse:
    ticker = ticker.upper()
    loop = asyncio.get_event_loop()
    master = await loop.run_in_executor(None, compute_master_signal, ticker)

    price = master.market_data.price
    price_history = await loop.run_in_executor(None, get_price_history, ticker)
    dark_pool_history = await loop.run_in_executor(None, get_dark_pool_history, ticker, price)
    gamma_history = await loop.run_in_executor(None, get_gamma_history, ticker, price)
    options_history = await loop.run_in_executor(None, get_options_flow, ticker, price)

    from engines.ai_signal_engine import get_ai_signal
    ai = get_ai_signal(
        ticker=ticker,
        options_flow_score=master.options_flow_score,
        dark_pool_net_flow=master.dark_pool.dark_pool_net_flow if master.dark_pool else 0,
        gamma_exposure=master.gamma.gamma_exposure if master.gamma else 0,
        short_interest=master.market_data.short_interest,
        volume_ratio=master.market_data.volume_ratio,
        insider_buying_flag=1 if master.insider_buying_score > 0 else 0,
        price_source_divergence=master.market_data.price_source_divergence,
    )

    return StockDetailResponse(
        ticker=ticker,
        market_data=master.market_data,
        master_signal=master,
        price_history=price_history,
        options_flow_history=options_history,
        dark_pool_history=dark_pool_history,
        gamma_history=gamma_history,
        insider_trades=master.insider_trades,
        ai_signal=ai,
    )
