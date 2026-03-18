"""
Insider Engine
Fetches SEC Form 4 filings from OpenInsider.com (transactions > $1M).
Falls back to seeded mock data when the network request fails.

Signal triggers when:
  transaction_value > 1_000_000  AND  role in qualifying executive roles
"""
import random
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from models.signals import InsiderTrade
from services.log_service import add_log, SOURCE_REAL, SOURCE_MOCK, SOURCE_ERROR

logger = logging.getLogger(__name__)

QUALIFYING_ROLES = {"CEO", "CFO", "Director", "Chairman", "President", "COO", "CTO", "CLO"}

# ── Fallback mock data ──────────────────────────────────────────────────────
_INSIDER_NAMES = [
    "Jensen Huang", "Satya Nadella", "Tim Cook", "Elon Musk", "Andy Jassy",
    "Sundar Pichai", "Mark Zuckerberg", "Lisa Su", "Reed Hastings",
    "Daniel Ek", "Brian Armstrong", "Vlad Tenev", "David Baszucki",
    "Frank Slootman", "Oliver Pocher", "Dan Schulman", "Jack Dorsey",
    "Dara Khosrowshahi", "Brian Chesky", "Bob Iger",
]
_ROLES = ["CEO", "CFO", "Director", "Director", "Chairman", "COO", "SVP", "EVP"]


def _seed(ticker: str) -> int:
    return sum(ord(c) * (i + 3) for i, c in enumerate(ticker))


# ── OpenInsider scraping ────────────────────────────────────────────────────

def _parse_value(s: str) -> float:
    """Parse OpenInsider value strings like '$1,234,567' → 1234567.0"""
    return float(s.replace("$", "").replace(",", "").strip() or "0")


def _parse_trade_type(raw: str) -> str:
    r = raw.strip().upper()
    if r.startswith("P"):
        return "buy"
    return "sell"


def _fetch_openinsider(ticker: str) -> Optional[List[InsiderTrade]]:
    """
    Scrape OpenInsider for trades > $1M for the given ticker.
    Returns None on any network/parse error so caller can use mock.
    """
    try:
        import httpx
        import certifi
        from bs4 import BeautifulSoup

        url = (
            f"https://openinsider.com/screener"
            f"?s={ticker}&o=&pl=1000000&ph=&ll=&lh=&fd=730&fdr=&td=0&tdr="
            f"&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=&vh=&ocl=&och="
            f"&sic1=-1&num=20&action=1"
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0 Safari/537.36"
            )
        }
        r = httpx.get(url, timeout=12, verify=certifi.where(), headers=headers)
        if r.status_code != 200:
            logger.warning("OpenInsider returned HTTP %s for %s", r.status_code, ticker)
            return None

        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table", {"class": "tinker"})
        if not table:
            return []

        trades: List[InsiderTrade] = []
        rows = table.find("tbody").find_all("tr") if table.find("tbody") else []

        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cols) < 12:
                continue
            # OpenInsider screener columns (0-indexed):
            # 0: (checkbox) 1: Filing Date  2: Trade Date  3: Ticker
            # 4: Company    5: Insider Name 6: Title       7: Trade Type
            # 8: Price      9: Qty          10: Owned      11: ΔOwn%  12: Value
            try:
                filing_date = cols[1].split()[0] if cols[1] else ""
                row_ticker   = cols[3].upper()
                insider_name = cols[5]
                title        = cols[6]
                trade_type   = _parse_trade_type(cols[7])
                price_str    = cols[8]
                qty_str      = cols[9].replace(",", "").replace("+", "").replace("-", "").strip()
                value_str    = cols[12] if len(cols) > 12 else "0"

                price = _parse_value(price_str)
                shares = int(qty_str) if qty_str.lstrip("-").isdigit() else 0
                value = _parse_value(value_str)

                if value < 1_000_000:
                    continue

                role_norm = title.upper()
                matched_role = "Director"
                for r_name in QUALIFYING_ROLES:
                    if r_name in role_norm:
                        matched_role = r_name
                        break

                score = 0.0
                if trade_type == "buy" and matched_role in QUALIFYING_ROLES:
                    score = min(100.0, value / 10_000_000 * 100)

                trades.append(InsiderTrade(
                    ticker=row_ticker or ticker,
                    insider_name=insider_name,
                    role=matched_role,
                    transaction_type=trade_type,
                    transaction_value=value,
                    shares=abs(shares),
                    price_per_share=round(price, 2),
                    filing_date=filing_date,
                    score=round(score, 2),
                ))
            except Exception:
                continue

        add_log("insider", ticker, SOURCE_REAL, f"OpenInsider scrape — {len(trades)} trades")
        return sorted(trades, key=lambda t: t.transaction_value, reverse=True)

    except Exception as exc:
        add_log("insider", ticker, SOURCE_ERROR, str(exc)[:120])
        logger.warning("OpenInsider fetch failed for %s: %s", ticker, exc)
        return None


# ── Mock fallback ───────────────────────────────────────────────────────────

def _mock_insider_trades(ticker: str, price: float) -> List[InsiderTrade]:
    rng = random.Random(_seed(ticker) + int(datetime.utcnow().day))
    trades: List[InsiderTrade] = []
    num_trades = rng.randint(0, 5)

    for _ in range(num_trades):
        role = rng.choice(_ROLES)
        transaction_type = rng.choice(["buy", "buy", "buy", "sell"])
        shares = rng.randint(1_000, 150_000)
        price_paid = price * rng.uniform(0.92, 1.02)
        value = round(shares * price_paid, 2)

        days_ago = rng.randint(1, 90)
        filing_date = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        score = 0.0
        if transaction_type == "buy" and role in QUALIFYING_ROLES and value > 250_000:
            score = min(100.0, value / 5_000_000 * 100)

        trades.append(InsiderTrade(
            ticker=ticker,
            insider_name=rng.choice(_INSIDER_NAMES),
            role=role,
            transaction_type=transaction_type,
            transaction_value=value,
            shares=shares,
            price_per_share=round(price_paid, 2),
            filing_date=filing_date,
            score=round(score, 2),
        ))

    return sorted(trades, key=lambda t: t.transaction_value, reverse=True)


# ── Public API ──────────────────────────────────────────────────────────────

def get_insider_trades(ticker: str, price: float) -> List[InsiderTrade]:
    """Return insider trades for ticker.  Real data when available, mock as fallback."""
    real = _fetch_openinsider(ticker)
    if real is not None:
        return real
    add_log("insider", ticker, SOURCE_MOCK, "OpenInsider unavailable — seeded mock")
    return _mock_insider_trades(ticker, price)


def compute_insider_score(trades: List[InsiderTrade]) -> float:
    """Score based on qualifying insider buys only (0–100)."""
    qualifying = [
        t for t in trades
        if t.transaction_type == "buy"
        and t.role in QUALIFYING_ROLES
        and t.transaction_value > 250_000
    ]
    if not qualifying:
        return 0.0
    total_value = sum(t.transaction_value for t in qualifying)
    return round(min(100.0, total_value / 10_000_000 * 100), 2)
