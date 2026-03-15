# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (local dev)
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`. Backend starts cleanly without PostgreSQL or Redis (both are optional — DB init and Redis cache failures are caught and logged as warnings).

Quick engine smoke test:
```bash
cd backend && source venv/bin/activate
python3 -c "from engines.market_data_engine import get_market_data; print(get_market_data('AAPL'))"
```

### Frontend (local dev)
```bash
cd frontend
npm install
npm run dev      # :3001 if 3000 is in use
npm run build
npm run lint
```

Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to point at either localhost or the deployed AWS URL.

### Full stack via Docker
```bash
docker-compose up --build
```

## Architecture

### Backend Signal Pipeline

`api/routes.py` → `services/signal_service.py` → 7 engines run in parallel via asyncio thread pool → weighted master score (0–100).

| Engine | Weight | File |
|--------|--------|------|
| Options flow | 20% | `engines/options_flow_engine.py` |
| Gamma exposure | 20% | `engines/gamma_exposure_engine.py` |
| Dark pool | 15% | `engines/dark_pool_engine.py` |
| Volume spike | 15% | `engines/market_data_engine.py` |
| Insider buying | 10% | `engines/insider_engine.py` |
| Institutional | 10% | `engines/institutional_flow_engine.py` |
| AI (XGBoost) | 10% | `engines/ai_signal_engine.py` |

Score thresholds: `85+` EXPLOSIVE · `70–84` STRONG_POSITIONING · `40–69` ACCUMULATION · `<40` WEAK.

### Real-time Market Data (Price Arbitrage Engine)

`engines/price_arbitrage_engine.py` fetches prices from up to 3 providers **in parallel** (ThreadPoolExecutor):

1. **Finnhub** (primary) — REST `/quote`, requires `FINNHUB_API_KEY`
2. **Yahoo Finance** (secondary) — via `yfinance`, free, no key needed; also provides market cap, 52w range, volume
3. **Alpha Vantage** (optional) — requires `ALPHA_VANTAGE_API_KEY`; free tier = 25 calls/day

`market_data_engine.get_market_data()` calls the arbitrage engine first and falls back to seeded mock data if all providers fail or no API key is set.

**Divergence detection:** if any two providers' prices differ by > 0.5%, `price_divergence_flag=True` and `price_source_divergence` (%) is set on the `MarketData` model. This feeds into the XGBoost model as a 7th feature.

Price history (`get_price_history()`) tries Finnhub `/stock/candle` → Yahoo Finance → mock.

### AI Signal Engine

XGBoost binary classifier (`engines/ai_signal_engine.py`) with 7 features:

| Feature | Source |
|---------|--------|
| `options_flow_score` | options engine |
| `dark_pool_net_flow_normalized` | dark pool engine |
| `gamma_exposure_normalized` | gamma engine |
| `short_interest` | market data engine |
| `volume_ratio` | market data engine |
| `insider_buying_flag` | insider engine |
| `price_source_divergence` | price arbitrage engine ← new |

Model trains on 5,000 synthetic samples at import time. Falls back to a heuristic formula if XGBoost is unavailable.

### Real Data: Insider Trades & Options Flow

**Insider Engine** (`engines/insider_engine.py`): Scrapes [OpenInsider.com](https://openinsider.com) for SEC Form 4 filings with transaction value > $1M (both purchases and sales, past 2 years). Uses `beautifulsoup4`/`lxml` to parse the `tinker` HTML table. Falls back to seeded mock data on any network/parse error.

**Options Flow Engine** (`engines/options_flow_engine.py`): Fetches live options chains from Yahoo Finance via `yfinance` (`Ticker.option_chain(expiry)`) for the 3 nearest expiry dates. Computes premium = lastPrice × volume × 100 and vol/OI ratio. Falls back to seeded mock data on failure.

Both engines use `logger.warning()` on failure — **no exception is raised**. This means behind Zscaler (local dev) or on transient network errors, the app silently uses mock data. On AWS App Runner the real data sources are active.

### SSL / Corporate Proxy

`main.py` calls `truststore.inject_into_ssl()` at startup to patch Python's SSL with the native OS trust store. Required when running behind Zscaler or other corporate proxies that install their own CA into the system keychain. On AWS (App Runner), this is a no-op and doesn't interfere.

### Caching

Redis caches the full signals list with 30s TTL (`cache_ttl_seconds` in `config.py`). Frontend SWR revalidates on the same 30s interval. Redis failures are caught silently — the app computes fresh data on every request when Redis is unavailable.

### Configuration

`backend/config.py` (Pydantic Settings) — all fields have defaults for local dev. Copy `.env.example` → `.env`:

| Variable | Required | Purpose |
|----------|----------|---------|
| `FINNHUB_API_KEY` | For live prices | Finnhub REST API |
| `ALPHA_VANTAGE_API_KEY` | Optional | 3rd price source for arbitrage |
| `DATABASE_URL` | Optional | PostgreSQL (has local default) |
| `REDIS_URL` | Optional | Redis cache (has local default) |
| `ALERT_WEBHOOK_URL` | Optional | Slack alerts on score > 85 |
| `SMTP_*` | Optional | Email alerts |

### Frontend

Next.js 14 Pages Router. Two pages: `pages/index.tsx` (dashboard) and `pages/stocks/[ticker].tsx` (stock detail). API client in `lib/api.ts` (Axios + SWR). TypeScript types in `lib/types.ts` mirror backend Pydantic models. Charts: Recharts for all widgets; `lightweight-charts` for the candlestick price chart.

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check |
| `GET /signals` | All 30 tickers ranked by master score (`?min_score=`, `?signal=`, `?limit=`) |
| `GET /stocks/{ticker}` | Full detail: scores, price history, options, dark pool, gamma, insiders, AI |
| `GET /options-flow` | Top tickers by options flow score |
| `GET /darkpool` | Top tickers by dark pool net flow |
| `GET /gamma` | Top tickers by gamma exposure score |
| `GET /ai-predictions` | Top tickers by XGBoost breakout probability |
| `GET /arbitrage` | Tickers with price divergence across providers (`?min_divergence=0.5`) |
| `GET /alerts` | Recent fired alerts |
| `GET /export/csv\|json\|excel` | Export full signals list |

## Deployment (AWS App Runner)

**Live URL:** `https://mh3ytbcc9w.us-east-1.awsapprunner.com`

- Region: `us-east-1`
- Runtime: Python 3.11, 1 vCPU / 2 GB RAM
- Auto-deploys on every push to `main` branch
- GitHub connection ARN: `arn:aws:apprunner:us-east-1:424683027978:connection/smart-money-github/bdf504c3ccdd4e1cb721307e6ddf6421`

**Key deployment details:**
- Packages installed into `/app/venv` during build (so they persist into the runtime image)
- Start command: `python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir backend`
- Build command: `python3 -m venv /app/venv && /app/venv/bin/pip install -r backend/requirements.txt`
- `FINNHUB_API_KEY` passed as runtime environment variable in the service config

To redeploy: `git push origin main` — App Runner triggers automatically.

To update service env vars:
```bash
aws apprunner update-service \
  --service-arn arn:aws:apprunner:us-east-1:424683027978:service/smart-money-backend/043f288c8a194075855c74ba73895b77 \
  --source-configuration '{"CodeRepository":{"CodeConfiguration":{"ConfigurationSource":"API","CodeConfigurationValues":{"RuntimeEnvironmentVariables":{"FINNHUB_API_KEY":"new_key"}}}}}' \
  --region us-east-1
```
