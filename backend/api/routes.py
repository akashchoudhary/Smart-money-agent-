"""
API Gateway — all HTTP routes for the Smart Money Intelligence Platform.
"""
import io
import json
import logging
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from services.signal_service import get_all_signals, get_stock_detail, compute_master_signal
from engines.alert_engine import get_recent_alerts
from models.signals import SignalResponse, StockDetailResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ------------------------------------------------------------------
# GET /signals  — ranked list of all tracked stocks
# ------------------------------------------------------------------
@router.get("/signals", response_model=List[SignalResponse])
async def list_signals(
    min_score: float = Query(0.0, description="Filter by minimum master score"),
    signal: Optional[str] = Query(None, description="bullish | bearish | neutral"),
    limit: int = Query(50, le=200),
):
    signals = await get_all_signals()
    if min_score > 0:
        signals = [s for s in signals if s.score >= min_score]
    if signal:
        signals = [s for s in signals if s.signal == signal.lower()]
    return signals[:limit]


# ------------------------------------------------------------------
# GET /stocks/{ticker}  — full detail for one ticker
# ------------------------------------------------------------------
@router.get("/stocks/{ticker}", response_model=StockDetailResponse)
async def get_stock(ticker: str):
    try:
        return await get_stock_detail(ticker.upper())
    except Exception as exc:
        logger.exception("Failed to fetch stock detail for %s", ticker)
        raise HTTPException(status_code=500, detail=str(exc))


# ------------------------------------------------------------------
# GET /options-flow  — top unusual options activity
# ------------------------------------------------------------------
@router.get("/options-flow")
async def options_flow(limit: int = Query(20, le=100)):
    signals = await get_all_signals()
    rows = []
    for s in signals:
        rows.append({
            "ticker": s.ticker,
            "options_flow_score": s.options_flow_score,
            "price": s.price,
            "signal": s.signal,
        })
    rows.sort(key=lambda r: r["options_flow_score"], reverse=True)
    return rows[:limit]


# ------------------------------------------------------------------
# GET /darkpool  — top dark pool activity
# ------------------------------------------------------------------
@router.get("/darkpool")
async def dark_pool(limit: int = Query(20, le=100)):
    signals = await get_all_signals()
    rows = [
        {
            "ticker": s.ticker,
            "dark_pool_flow": s.dark_pool_flow,
            "price": s.price,
            "signal": s.signal,
        }
        for s in signals
    ]
    rows.sort(key=lambda r: r["dark_pool_flow"], reverse=True)
    return rows[:limit]


# ------------------------------------------------------------------
# GET /gamma  — gamma exposure summary
# ------------------------------------------------------------------
@router.get("/gamma")
async def gamma_summary(limit: int = Query(20, le=100)):
    signals = await get_all_signals()
    rows = [
        {
            "ticker": s.ticker,
            "gamma_score": s.gamma_score,
            "price": s.price,
            "signal": s.signal,
        }
        for s in signals
    ]
    rows.sort(key=lambda r: r["gamma_score"], reverse=True)
    return rows[:limit]


# ------------------------------------------------------------------
# GET /ai-predictions  — AI breakout predictions
# ------------------------------------------------------------------
@router.get("/ai-predictions")
async def ai_predictions(limit: int = Query(20, le=100)):
    signals = await get_all_signals()
    rows = [
        {
            "ticker": s.ticker,
            "breakout_probability": s.breakout_probability,
            "score": s.score,
            "signal": s.signal,
            "price": s.price,
            "change_pct": s.change_pct,
        }
        for s in signals
    ]
    rows.sort(key=lambda r: r["breakout_probability"], reverse=True)
    return rows[:limit]


# ------------------------------------------------------------------
# GET /alerts  — recent fired alerts
# ------------------------------------------------------------------
@router.get("/alerts")
async def alerts(limit: int = Query(50, le=200)):
    return get_recent_alerts(limit)


# ------------------------------------------------------------------
# Export endpoints
# ------------------------------------------------------------------
@router.get("/export/csv")
async def export_csv():
    signals = await get_all_signals()
    df = pd.DataFrame([s.model_dump() for s in signals])
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=smart_money_signals.csv"},
    )


@router.get("/export/json")
async def export_json():
    signals = await get_all_signals()
    content = json.dumps([s.model_dump() for s in signals], default=str, indent=2)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=smart_money_signals.json"},
    )


@router.get("/export/excel")
async def export_excel():
    signals = await get_all_signals()
    df = pd.DataFrame([s.model_dump() for s in signals])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Signals", index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=smart_money_signals.xlsx"},
    )
