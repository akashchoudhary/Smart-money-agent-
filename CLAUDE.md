# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload          # dev server on :8000
```

Single-file test (no test framework configured):
```bash
cd backend && python -c "from engines.ai_signal_engine import AISignalEngine; e = AISignalEngine(); print(e.get_signal('NVDA'))"
```

API docs auto-generated at `http://localhost:8000/docs` when running.

### Frontend
```bash
cd frontend
npm install
npm run dev      # dev server on :3000
npm run build    # production build
npm run lint     # ESLint
```

### Full Stack (Docker)
```bash
docker-compose up --build    # starts postgres, redis, backend, frontend
```

Backend requires PostgreSQL + Redis running. For local dev without Docker:
```bash
# Start only infra
docker-compose up postgres redis
```

## Architecture

### Backend Signal Pipeline

All logic flows through `services/signal_service.py`, which orchestrates the 7 engines in parallel via asyncio and computes a weighted master score (0-100):

| Engine | Weight | File |
|--------|--------|------|
| Options flow | 20% | `engines/options_flow_engine.py` |
| Gamma exposure | 20% | `engines/gamma_exposure_engine.py` |
| Dark pool | 15% | `engines/dark_pool_engine.py` |
| Volume spike | 15% | `engines/market_data_engine.py` |
| Insider buying | 10% | `engines/insider_engine.py` |
| Institutional | 10% | `engines/institutional_flow_engine.py` |
| AI (XGBoost) | 10% | `engines/ai_signal_engine.py` |

Master score thresholds → signal strength: `85+` = EXPLOSIVE, `70-84` = STRONG_POSITIONING, `40-69` = ACCUMULATION, `<40` = WEAK.

### Data
All 30 tracked tickers use **deterministic mock/simulated data** seeded by ticker name + current UTC hour. No live market data feed is connected. The stock universe is hardcoded in `engines/market_data_engine.py`.

### Caching
Redis caches the full signals list with a 30s TTL (configurable via `cache_ttl_seconds` in `config.py`). The frontend uses SWR with matching 30s revalidation.

### Configuration
Backend settings live in `backend/config.py` (Pydantic Settings). Copy `backend/.env.example` → `backend/.env` to override defaults. Required only for alerts: `ALERT_WEBHOOK_URL` (Slack) and SMTP creds. The database/redis URLs have working defaults for local dev.

### Frontend
Next.js 14 Pages Router. Two pages: `pages/index.tsx` (dashboard) and `pages/stocks/[ticker].tsx` (detail). API client is `lib/api.ts` (Axios). TypeScript types mirror backend Pydantic models in `lib/types.ts`. All charts use Recharts except the price candlestick which uses `lightweight-charts`.

### Alerts
`engines/alert_engine.py` fires asynchronously when `master_score > 85`. Sends Slack webhook and/or email if credentials are set in `.env`.
