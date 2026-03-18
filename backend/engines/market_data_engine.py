"""
Market Data Engine
Fetches price, volume, and market data for tracked tickers.

Primary:  Finnhub REST /quote  (real-time)
Secondary: Yahoo Finance        (supplementary & fallback)
Tertiary:  Alpha Vantage        (optional divergence check)
Fallback:  Mock/seeded data     (when all APIs unavailable)
"""
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import certifi
import httpx
import numpy as np

_SSL_VERIFY = certifi.where()

from config import get_settings
from engines.price_arbitrage_engine import fetch_multi_provider, ArbitrageResult
from models.signals import MarketData, PricePoint
from services.log_service import add_log, SOURCE_REAL, SOURCE_MOCK, SOURCE_ERROR

logger = logging.getLogger(__name__)

UNIVERSE = [
    "NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "AMD",
    "NFLX", "SPY", "QQQ", "PLTR", "RIVN", "SOFI", "GME", "MARA",
    "COIN", "HOOD", "RBLX", "SNOW", "DDOG", "PYPL", "SQ", "UBER",
    "ABNB", "DIS", "BA", "JPM", "GS", "MS"
]

# Fallback mock data (used when real APIs unavailable)
_BASE_PRICES: Dict[str, float] = {
    "NVDA": 875.0, "AAPL": 182.0, "MSFT": 415.0, "TSLA": 248.0,
    "AMZN": 192.0, "GOOGL": 167.0, "META": 498.0, "AMD": 175.0,
    "NFLX": 623.0, "SPY": 521.0, "QQQ": 448.0, "PLTR": 22.0,
    "RIVN": 11.0,  "SOFI": 7.5,   "GME": 16.0,   "MARA": 18.0,
    "COIN": 225.0, "HOOD": 18.0,  "RBLX": 38.0,  "SNOW": 152.0,
    "DDOG": 125.0, "PYPL": 63.0,  "SQ": 72.0,    "UBER": 78.0,
    "ABNB": 163.0, "DIS": 112.0,  "BA": 195.0,   "JPM": 198.0,
    "GS": 432.0,   "MS": 102.0,
}

_BASE_MCAP: Dict[str, float] = {
    "NVDA": 2_150_000_000_000, "AAPL": 2_800_000_000_000,
    "MSFT": 3_080_000_000_000, "TSLA": 790_000_000_000,
    "AMZN": 1_980_000_000_000, "GOOGL": 2_100_000_000_000,
    "META": 1_270_000_000_000, "AMD": 283_000_000_000,
    "NFLX": 272_000_000_000,   "SPY": 490_000_000_000,
    "QQQ": 245_000_000_000,    "PLTR": 46_000_000_000,
    "RIVN": 10_500_000_000,    "SOFI": 7_200_000_000,
    "GME": 4_900_000_000,      "MARA": 3_800_000_000,
    "COIN": 55_000_000_000,    "HOOD": 15_200_000_000,
    "RBLX": 24_000_000_000,    "SNOW": 51_000_000_000,
    "DDOG": 40_000_000_000,    "PYPL": 67_000_000_000,
    "SQ": 43_000_000_000,      "UBER": 162_000_000_000,
    "ABNB": 104_000_000_000,   "DIS": 205_000_000_000,
    "BA": 114_000_000_000,     "JPM": 568_000_000_000,
    "GS": 141_000_000_000,     "MS": 170_000_000_000,
}


def _seed(ticker: str) -> int:
    return sum(ord(c) for c in ticker)


# ---------------------------------------------------------------------------
# Mock fallback (unchanged from original — used when APIs unavailable)
# ---------------------------------------------------------------------------

def _mock_market_data(ticker: str) -> MarketData:
    rng = random.Random(_seed(ticker) + int(datetime.utcnow().hour))
    base_price = _BASE_PRICES.get(ticker, 50.0)
    price = round(base_price * (1 + rng.uniform(-0.03, 0.05)), 2)
    change_pct = round(rng.uniform(-4.5, 6.5), 2)
    avg_vol = int(rng.uniform(5_000_000, 80_000_000))
    vol_multiplier = rng.choice([1.0, 1.2, 1.5, 2.1, 3.4, 4.2])
    volume = int(avg_vol * vol_multiplier)
    return MarketData(
        ticker=ticker,
        price=price,
        change_pct=change_pct,
        volume=volume,
        avg_volume_30d=avg_vol,
        volume_ratio=round(volume / avg_vol, 2),
        market_cap=_BASE_MCAP.get(ticker, 10_000_000_000),
        short_interest=round(rng.uniform(0.01, 0.35), 4),
        high_52w=round(price * rng.uniform(1.05, 1.6), 2),
        low_52w=round(price * rng.uniform(0.45, 0.92), 2),
        price_divergence_flag=False,
        price_source_divergence=0.0,
        data_sources=["mock"],
    )


def _mock_price_history(ticker: str, days: int = 90) -> List[PricePoint]:
    rng = random.Random(_seed(ticker))
    price = _BASE_PRICES.get(ticker, 50.0) * rng.uniform(0.75, 0.95)
    points: List[PricePoint] = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - i)
        price = max(price * (1 + rng.gauss(0.001, 0.022)), 1.0)
        points.append(PricePoint(
            time=date.strftime("%Y-%m-%d"),
            open=round(price * rng.uniform(0.995, 1.005), 2),
            high=round(price * rng.uniform(1.002, 1.025), 2),
            low=round(price * rng.uniform(0.975, 0.998), 2),
            close=round(price, 2),
            volume=int(rng.uniform(3_000_000, 60_000_000)),
        ))
    return points


# ---------------------------------------------------------------------------
# Real data assembly
# ---------------------------------------------------------------------------

def _build_market_data_from_arbitrage(ticker: str, arb: ArbitrageResult) -> Optional[MarketData]:
    """Assemble a MarketData from real provider data. Returns None if no usable data."""
    bq   = arb.best_quote
    supp = arb.supplementary

    if bq is None or bq.price <= 0:
        return None

    rng = random.Random(_seed(ticker))  # for fields we can't get from free APIs
    base_price = bq.price

    # Volume — prefer Yahoo supplementary, then best_quote, then mock estimate
    avg_vol    = (supp.avg_volume_30d if supp and supp.avg_volume_30d > 0
                  else int(rng.uniform(5_000_000, 80_000_000)))
    vol_today  = (supp.volume_today if supp and supp.volume_today > 0
                  else bq.volume if bq.volume > 0
                  else int(avg_vol * rng.choice([1.0, 1.2, 1.5, 2.1])))
    vol_ratio  = round(vol_today / avg_vol, 2) if avg_vol > 0 else 1.0

    # Market cap — Yahoo supplementary preferred, else static fallback
    mkt_cap = (supp.market_cap if supp and supp.market_cap > 0
               else _BASE_MCAP.get(ticker, 10_000_000_000))

    # 52-week range — Yahoo supplementary preferred
    high_52w = (supp.high_52w if supp and supp.high_52w > 0
                else round(base_price * 1.35, 2))
    low_52w  = (supp.low_52w if supp and supp.low_52w > 0
                else round(base_price * 0.65, 2))

    # Short interest — not available from free sources; use seeded mock
    short_interest = round(rng.uniform(0.01, 0.35), 4)

    return MarketData(
        ticker=ticker,
        price=round(base_price, 2),
        change_pct=round(bq.change_pct, 4),
        volume=vol_today,
        avg_volume_30d=avg_vol,
        volume_ratio=vol_ratio,
        market_cap=mkt_cap,
        short_interest=short_interest,
        high_52w=high_52w,
        low_52w=low_52w,
        price_divergence_flag=arb.is_anomaly,
        price_source_divergence=arb.divergence_pct,
        data_sources=arb.sources,
    )


def _fetch_finnhub_candles(ticker: str, days: int, api_key: str) -> Optional[List[PricePoint]]:
    """Fetch OHLCV candle history from Finnhub /stock/candle."""
    try:
        now   = int(time.time())
        from_ = now - days * 86400
        resp = httpx.get(
            f"https://finnhub.io/api/v1/stock/candle",
            params={
                "symbol":     ticker,
                "resolution": "D",
                "from":       from_,
                "to":         now,
                "token":      api_key,
            },
            timeout=8.0,
            verify=_SSL_VERIFY,
        )
        resp.raise_for_status()
        d = resp.json()
        if d.get("s") != "ok" or not d.get("t"):
            return None

        points = []
        for i, ts in enumerate(d["t"]):
            points.append(PricePoint(
                time=datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"),
                open=round(d["o"][i], 2),
                high=round(d["h"][i], 2),
                low=round(d["l"][i], 2),
                close=round(d["c"][i], 2),
                volume=int(d["v"][i]),
            ))
        return points if points else None
    except Exception as exc:
        logger.warning("Finnhub candles failed for %s: %s", ticker, exc)
        return None


def _fetch_yahoo_candles(ticker: str, days: int) -> Optional[List[PricePoint]]:
    """Fetch OHLCV candle history from Yahoo Finance via yfinance."""
    try:
        import yfinance as yf
        hist = yf.Ticker(ticker).history(period=f"{days}d", interval="1d")
        if hist.empty:
            return None
        points = []
        for ts, row in hist.iterrows():
            points.append(PricePoint(
                time=ts.strftime("%Y-%m-%d"),
                open=round(float(row["Open"]), 2),
                high=round(float(row["High"]), 2),
                low=round(float(row["Low"]), 2),
                close=round(float(row["Close"]), 2),
                volume=int(row["Volume"]),
            ))
        return points if points else None
    except Exception as exc:
        logger.warning("Yahoo candles failed for %s: %s", ticker, exc)
        return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_market_data(ticker: str) -> MarketData:
    settings = get_settings()
    if settings.finnhub_api_key:
        try:
            arb = fetch_multi_provider(
                ticker,
                finnhub_key=settings.finnhub_api_key,
                av_key=settings.alpha_vantage_api_key,
            )
            md = _build_market_data_from_arbitrage(ticker, arb)
            if md is not None:
                sources_str = "+".join(md.data_sources) or "unknown"
                add_log("price", ticker, SOURCE_REAL, f"{sources_str} — divergence {md.price_source_divergence:.2f}%")
                return md
            logger.warning("Real data returned empty for %s, using mock", ticker)
        except Exception as exc:
            add_log("price", ticker, SOURCE_ERROR, str(exc)[:120])
            logger.warning("Real data fetch failed for %s, using mock: %s", ticker, exc)

    add_log("price", ticker, SOURCE_MOCK, "No API key or all providers failed")
    return _mock_market_data(ticker)


def get_price_history(ticker: str, days: int = 90) -> List[PricePoint]:
    settings = get_settings()
    if settings.finnhub_api_key:
        points = _fetch_finnhub_candles(ticker, days, settings.finnhub_api_key)
        if points:
            return points

    # Yahoo fallback
    try:
        points = _fetch_yahoo_candles(ticker, days)
        if points:
            return points
    except Exception:
        pass

    return _mock_price_history(ticker, days)


def compute_volume_spike_score(market_data: MarketData) -> float:
    ratio = market_data.volume_ratio
    if ratio < 1.0:
        return 0.0
    if ratio >= 5.0:
        return 100.0
    return min(100.0, (ratio - 1.0) / 4.0 * 100.0)


def get_universe() -> List[str]:
    return UNIVERSE
