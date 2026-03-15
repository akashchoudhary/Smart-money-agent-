"""
Price Arbitrage Engine
Fetches real-time quotes from multiple providers and detects price divergence.

Providers:
  1. Finnhub        (primary)  — REST /quote, real-time
  2. Yahoo Finance  (secondary) — yfinance fast_info, free / no key
  3. Alpha Vantage  (optional)  — REST GLOBAL_QUOTE, set ALPHA_VANTAGE_API_KEY

Anomaly: if any two providers diverge by > DIVERGENCE_THRESHOLD_PCT, flag it.
A divergence > 0.5% indicates latency arbitrage opportunity or data anomaly.
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import certifi
import httpx

logger = logging.getLogger(__name__)

# Use certifi CA bundle — required on macOS when Python installed from python.org
_SSL_VERIFY = certifi.where()

DIVERGENCE_THRESHOLD_PCT = 0.5   # flag if providers differ by more than this %
FINNHUB_BASE = "https://finnhub.io/api/v1"
AV_BASE      = "https://www.alphavantage.co/query"
TIMEOUT      = 5.0               # seconds per provider call


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ProviderQuote:
    source:     str
    price:      float
    change_pct: float = 0.0
    volume:     int   = 0
    high:       float = 0.0
    low:        float = 0.0
    open:       float = 0.0


@dataclass
class SupplementaryData:
    """Non-price market data fetched from Yahoo Finance."""
    market_cap:     float = 0.0
    avg_volume_30d: int   = 0
    volume_today:   int   = 0
    high_52w:       float = 0.0
    low_52w:        float = 0.0
    short_interest: float = 0.0   # not reliably free; kept as 0.0 fallback


@dataclass
class ArbitrageResult:
    ticker:         str
    quotes:         List[ProviderQuote] = field(default_factory=list)
    best_quote:     Optional[ProviderQuote] = None
    supplementary:  Optional[SupplementaryData] = None
    divergence_pct: float = 0.0
    is_anomaly:     bool  = False
    sources:        List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual provider fetchers (all synchronous — called from thread pool)
# ---------------------------------------------------------------------------

def fetch_finnhub_quote(ticker: str, api_key: str) -> Optional[ProviderQuote]:
    try:
        resp = httpx.get(
            f"{FINNHUB_BASE}/quote",
            params={"symbol": ticker, "token": api_key},
            timeout=TIMEOUT,
            verify=_SSL_VERIFY,
        )
        resp.raise_for_status()
        d = resp.json()
        price = float(d.get("c", 0))
        if price <= 0:
            logger.debug("Finnhub returned zero price for %s", ticker)
            return None
        return ProviderQuote(
            source="finnhub",
            price=price,
            change_pct=float(d.get("dp", 0.0)),
            volume=0,   # /quote doesn't include volume; use supplementary
            high=float(d.get("h", price)),
            low=float(d.get("l", price)),
            open=float(d.get("o", price)),
        )
    except Exception as exc:
        logger.warning("Finnhub quote failed for %s: %s", ticker, exc)
        return None


def fetch_yahoo_quote(ticker: str) -> Optional[ProviderQuote]:
    try:
        import yfinance as yf
        fi = yf.Ticker(ticker).fast_info
        price = float(fi.last_price or 0)
        if price <= 0:
            return None
        prev_close = float(fi.previous_close or price)
        change_pct = round((price - prev_close) / prev_close * 100, 4) if prev_close else 0.0
        return ProviderQuote(
            source="yahoo",
            price=price,
            change_pct=change_pct,
            volume=int(getattr(fi, "last_volume", 0) or 0),
            high=float(getattr(fi, "day_high", price) or price),
            low=float(getattr(fi, "day_low", price) or price),
            open=float(getattr(fi, "open", price) or price),
        )
    except Exception as exc:
        logger.warning("Yahoo Finance quote failed for %s: %s", ticker, exc)
        return None


def fetch_alphavantage_quote(ticker: str, api_key: str) -> Optional[ProviderQuote]:
    try:
        resp = httpx.get(
            AV_BASE,
            params={"function": "GLOBAL_QUOTE", "symbol": ticker, "apikey": api_key},
            timeout=TIMEOUT,
            verify=_SSL_VERIFY,
        )
        resp.raise_for_status()
        gq = resp.json().get("Global Quote", {})
        price_str = gq.get("05. price", "0")
        price = float(price_str)
        if price <= 0:
            return None
        change_pct = float(gq.get("10. change percent", "0%").replace("%", ""))
        return ProviderQuote(
            source="alphavantage",
            price=price,
            change_pct=change_pct,
            volume=int(gq.get("06. volume", 0)),
            high=float(gq.get("03. high", price)),
            low=float(gq.get("04. low", price)),
            open=float(gq.get("02. open", price)),
        )
    except Exception as exc:
        logger.warning("Alpha Vantage quote failed for %s: %s", ticker, exc)
        return None


def fetch_yahoo_supplementary(ticker: str) -> SupplementaryData:
    """Fetch non-price data (market cap, volume, 52w range) from Yahoo Finance."""
    try:
        import yfinance as yf
        fi = yf.Ticker(ticker).fast_info
        return SupplementaryData(
            market_cap=float(getattr(fi, "market_cap", 0) or 0),
            avg_volume_30d=int(getattr(fi, "three_month_average_volume", 0) or 0),
            volume_today=int(getattr(fi, "last_volume", 0) or 0),
            high_52w=float(getattr(fi, "fifty_two_week_high", 0) or 0),
            low_52w=float(getattr(fi, "fifty_two_week_low", 0) or 0),
            short_interest=0.0,  # requires premium data source
        )
    except Exception as exc:
        logger.warning("Yahoo supplementary data failed for %s: %s", ticker, exc)
        return SupplementaryData()


# ---------------------------------------------------------------------------
# Multi-provider orchestrator
# ---------------------------------------------------------------------------

def fetch_multi_provider(
    ticker: str,
    finnhub_key: str,
    av_key: str = "",
) -> ArbitrageResult:
    """
    Fetch price quotes from all available providers in parallel.
    Returns an ArbitrageResult with divergence analysis.
    """
    result = ArbitrageResult(ticker=ticker)

    futures: Dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=4) as exe:
        futures["finnhub"]       = exe.submit(fetch_finnhub_quote, ticker, finnhub_key)
        futures["yahoo"]         = exe.submit(fetch_yahoo_quote, ticker)
        futures["supplementary"] = exe.submit(fetch_yahoo_supplementary, ticker)
        if av_key:
            futures["alphavantage"] = exe.submit(fetch_alphavantage_quote, ticker, av_key)

    quotes: Dict[str, ProviderQuote] = {}
    for source, fut in futures.items():
        try:
            value = fut.result(timeout=TIMEOUT + 1)
            if source == "supplementary":
                result.supplementary = value
            elif value is not None:
                quotes[source] = value
        except Exception as exc:
            logger.warning("Provider %s timed out for %s: %s", source, ticker, exc)

    result.quotes  = list(quotes.values())
    result.sources = list(quotes.keys())

    # Pick best quote: Finnhub > Yahoo > Alpha Vantage
    result.best_quote = (
        quotes.get("finnhub")
        or quotes.get("yahoo")
        or quotes.get("alphavantage")
    )

    # Compute divergence across all available price sources
    if len(quotes) >= 2:
        prices = [q.price for q in quotes.values() if q.price > 0]
        if prices:
            span = max(prices) - min(prices)
            result.divergence_pct = round(span / min(prices) * 100, 4)
            result.is_anomaly     = result.divergence_pct > DIVERGENCE_THRESHOLD_PCT

    return result
