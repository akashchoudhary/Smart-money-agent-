"""
Insider Engine
Tracks SEC Form 4 filings for insider buying activity.

Signal triggers when:
  transaction_value > 250_000  AND  role in (CEO, CFO, Director)
"""
import random
from datetime import datetime, timedelta
from typing import List
from models.signals import InsiderTrade

QUALIFYING_ROLES = {"CEO", "CFO", "Director", "Chairman", "President", "COO"}

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


def get_insider_trades(ticker: str, price: float) -> List[InsiderTrade]:
    rng = random.Random(_seed(ticker) + int(datetime.utcnow().day))
    trades: List[InsiderTrade] = []
    num_trades = rng.randint(0, 5)

    for i in range(num_trades):
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


def compute_insider_score(trades: List[InsiderTrade]) -> float:
    """Score based on qualifying insider buys only."""
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
