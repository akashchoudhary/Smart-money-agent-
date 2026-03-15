# Smart Money Intelligence Platform — Backend

FastAPI backend that detects institutional activity across 30 tracked tickers using 7 signal engines and an XGBoost breakout predictor.

**Live API:** `https://mh3ytbcc9w.us-east-1.awsapprunner.com`
**API Docs:** `https://mh3ytbcc9w.us-east-1.awsapprunner.com/docs`

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your FINNHUB_API_KEY
uvicorn main:app --reload --port 8000
```

Runs on `http://localhost:8000`. PostgreSQL and Redis are optional — the app falls back gracefully without them.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `FINNHUB_API_KEY` | Yes (for live prices) | Get free key at [finnhub.io](https://finnhub.io) |
| `ALPHA_VANTAGE_API_KEY` | No | 3rd price source for arbitrage detection (25 calls/day free) |
| `DATABASE_URL` | No | PostgreSQL connection string (has working default) |
| `REDIS_URL` | No | Redis for signal caching (has working default) |
| `ALERT_WEBHOOK_URL` | No | Slack webhook — fires when master score > 85 |
| `SMTP_HOST/PORT/USER/PASS` | No | Email alerts |
| `MASTER_SCORE_ALERT_THRESHOLD` | No | Default: 85.0 |
| `CACHE_TTL_SECONDS` | No | Default: 30 |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/signals` | All tickers ranked by master score |
| GET | `/stocks/{ticker}` | Full detail for one ticker |
| GET | `/options-flow` | Top unusual options activity |
| GET | `/darkpool` | Top dark pool flows |
| GET | `/gamma` | Gamma exposure summary |
| GET | `/ai-predictions` | XGBoost breakout probabilities |
| GET | `/arbitrage` | Price divergence across providers |
| GET | `/alerts` | Recent fired alerts |
| GET | `/export/csv` | Download signals as CSV |
| GET | `/export/json` | Download signals as JSON |
| GET | `/export/excel` | Download signals as Excel |

**Query params for `/signals`:** `?min_score=70`, `?signal=bullish`, `?limit=20`
**Query params for `/arbitrage`:** `?min_divergence=0.5`

---

## Architecture

### Signal Pipeline

```
GET /signals
    └── signal_service.py
            ├── market_data_engine.py    (price, volume, market cap)
            │       └── price_arbitrage_engine.py  (Finnhub + Yahoo + Alpha Vantage)
            ├── options_flow_engine.py   (unusual options activity)
            ├── dark_pool_engine.py      (institutional block trades)
            ├── gamma_exposure_engine.py (dealer gamma / GEX)
            ├── insider_engine.py        (SEC Form 4 filings)
            ├── institutional_flow_engine.py (ETF flows, block trades)
            └── ai_signal_engine.py      (XGBoost breakout predictor)
```

All 30 tickers are processed concurrently via `asyncio.gather` + thread pool executor.

### Master Score Weights

| Signal | Weight |
|--------|--------|
| Options flow score | 20% |
| Gamma exposure score | 20% |
| Dark pool score | 15% |
| Volume spike score | 15% |
| Insider buying score | 10% |
| Institutional flow score | 10% |
| AI (XGBoost) score | 10% |

**Score → Signal Strength:** `85+` EXPLOSIVE · `70–84` STRONG_POSITIONING · `40–69` ACCUMULATION · `<40` WEAK

### Price Arbitrage Engine

Fetches real-time quotes from multiple providers in parallel and flags divergence:

- **Finnhub** — primary real-time quote (`/api/v1/quote`)
- **Yahoo Finance** — secondary quote + supplementary data (market cap, 52w range, volume) via `yfinance`
- **Alpha Vantage** — optional 3rd source (set `ALPHA_VANTAGE_API_KEY`)

If any two providers differ by > **0.5%**, `price_divergence_flag=True` is set on the response. This divergence value also feeds into the XGBoost model as a 7th feature (latency arbitrage signal).

### AI Signal Engine

XGBoost binary classifier trained on 5,000 synthetic samples with 7 features:
`options_flow_score`, `dark_pool_net_flow`, `gamma_exposure`, `short_interest`, `volume_ratio`, `insider_buying_flag`, `price_source_divergence`

Output: `breakout_probability` (0.0–1.0). Falls back to a heuristic formula if XGBoost is unavailable.

### Data Sources

- **Live prices:** Finnhub REST API (real-time) + Yahoo Finance (fallback)
- **Options, dark pool, gamma, insider, institutional:** Simulated/mock data (deterministic, seeded by ticker). Replace each engine's `get_*()` function with a real data provider to go fully live.
- **Short interest:** Mock (not available from free sources)

---

## Project Structure

```
backend/
├── main.py                          # FastAPI app, lifespan, CORS, truststore SSL patch
├── config.py                        # Pydantic Settings (reads from .env)
├── database.py                      # SQLAlchemy async setup
├── requirements.txt
├── Dockerfile
├── .env.example
├── api/
│   └── routes.py                    # All HTTP endpoints
├── models/
│   └── signals.py                   # Pydantic models (shared between engines and API)
├── services/
│   └── signal_service.py            # Orchestration, master score, Redis caching
└── engines/
    ├── price_arbitrage_engine.py    # Multi-provider real-time price fetching
    ├── market_data_engine.py        # Price history, volume, market cap
    ├── options_flow_engine.py       # Options activity detection
    ├── dark_pool_engine.py          # Dark pool flow tracking
    ├── gamma_exposure_engine.py     # Gamma exposure / GEX
    ├── insider_engine.py            # SEC Form 4 insider trades
    ├── institutional_flow_engine.py # Block trades, ETF flows
    ├── ai_signal_engine.py          # XGBoost breakout predictor
    └── alert_engine.py              # Slack/email alert firing
```

---

## Deployment (AWS App Runner)

The service auto-deploys on every push to `main`.

**Build command:**
```
python3 -m venv /app/venv && /app/venv/bin/pip install -r backend/requirements.txt
```

**Start command:**
```
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir backend
```

To deploy manually:
```bash
git add . && git commit -m "your changes" && git push origin main
```

To check service status:
```bash
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-east-1:424683027978:service/smart-money-backend/043f288c8a194075855c74ba73895b77 \
  --region us-east-1 \
  --query 'Service.Status' --output text
```

---

## Notes

- **Zscaler / corporate proxy:** `truststore` is installed and injected at startup so Python uses the OS keychain for SSL certificate verification. This is required locally but harmless on AWS.
- **No PostgreSQL needed locally:** The database is initialized on startup but failures are swallowed. Signal data is computed in-memory and cached in Redis.
- **Connecting real data sources:** Each engine has a clear `get_*()` function to replace. See `CLAUDE.md` for the replacement guide.
