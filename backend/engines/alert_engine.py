"""
Alert Engine
Fires webhook and email alerts when MasterScore > threshold (default 85).
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
import httpx
from models.signals import AlertPayload, MasterSignal
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_alert_log: list[dict] = []  # in-memory log (use DB in production)


async def _send_webhook(payload: AlertPayload) -> bool:
    if not settings.alert_webhook_url:
        return False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                settings.alert_webhook_url,
                json={
                    "text": (
                        f":rotating_light: *SMART MONEY ALERT* — `{payload.ticker}`\n"
                        f"Score: *{payload.master_score:.1f}* | "
                        f"Breakout Prob: *{payload.breakout_probability:.0%}* | "
                        f"Signal: *{payload.signal.upper()}*\n"
                        f"Dark Pool Flow: ${payload.dark_pool_flow:,.0f}"
                    )
                },
            )
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("Webhook delivery failed: %s", exc)
        return False


async def _send_email(payload: AlertPayload) -> bool:
    """Stub — wire up aiosmtplib / SendGrid / SES in production."""
    if not settings.alert_email or not settings.smtp_user:
        return False
    try:
        import aiosmtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = f"[Smart Money Alert] {payload.ticker} — Score {payload.master_score:.1f}"
        msg["From"] = settings.smtp_user
        msg["To"] = settings.alert_email
        msg.set_content(
            f"Ticker: {payload.ticker}\n"
            f"Master Score: {payload.master_score:.1f}\n"
            f"Breakout Probability: {payload.breakout_probability:.0%}\n"
            f"Signal: {payload.signal}\n"
            f"Dark Pool Flow: ${payload.dark_pool_flow:,.0f}\n"
            f"Timestamp: {payload.timestamp.isoformat()}"
        )
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_pass,
            start_tls=True,
        )
        return True
    except Exception as exc:
        logger.warning("Email delivery failed: %s", exc)
        return False


async def check_and_fire(signal: MasterSignal) -> Optional[AlertPayload]:
    """
    Evaluate a MasterSignal and fire alerts if score exceeds threshold.
    Returns the AlertPayload if an alert was fired, else None.
    """
    if signal.master_score < settings.master_score_alert_threshold:
        return None

    payload = AlertPayload(
        ticker=signal.ticker,
        master_score=signal.master_score,
        breakout_probability=signal.breakout_probability,
        signal=signal.direction.value,
        dark_pool_flow=signal.dark_pool.dark_pool_net_flow if signal.dark_pool else 0.0,
        timestamp=datetime.utcnow(),
    )

    _alert_log.append(payload.model_dump())
    logger.info("ALERT fired for %s — score %.1f", signal.ticker, signal.master_score)

    await asyncio.gather(
        _send_webhook(payload),
        _send_email(payload),
        return_exceptions=True,
    )

    return payload


def get_recent_alerts(limit: int = 50) -> list[dict]:
    return _alert_log[-limit:]
