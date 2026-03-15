# Smart Money Intelligence Platform — Frontend

Next.js 14 dashboard for real-time institutional signal monitoring. Displays options flow, dark pool activity, gamma exposure, insider trades, and AI breakout predictions across 30 tracked tickers.

---

## Quick Start

```bash
npm install
npm run dev      # http://localhost:3000 (or 3001 if 3000 is in use)
npm run build    # production build
npm run lint
```

Requires the backend running at the URL set in `.env.local`.

---

## Environment Variables

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000          # local dev
# NEXT_PUBLIC_API_URL=https://mh3ytbcc9w.us-east-1.awsapprunner.com  # AWS
```

---

## Pages

### Dashboard (`/`)

Main signal monitoring screen.

- **Stat cards** — live counts: tracked tickers, explosive setups, strong positioning, bullish signals
- **Filters** — filter by min score (All / 40+ / 70+ / 85+) and signal direction (bullish / bearish / neutral)
- **Signals table** — all 30 tickers sortable by score, price, options flow, gamma, dark pool, breakout probability
- **Widget row** — Gamma Radar, Dark Pool Feed, Options Flow Tape, AI Breakout Signals

All data refreshes every **30 seconds** via SWR.

### Stock Detail (`/stocks/[ticker]`)

Deep-dive page for a single ticker.

- Master score gauge + 7 sub-score breakdown bars
- AI prediction panel (breakout probability, confidence, feature weights)
- 90-day price chart (candlestick via `lightweight-charts`)
- Dark pool net flow history (30 days)
- Gamma exposure history (30 days)
- Options flow by strike (bar chart)
- Insider trades table (top 5 filings)

---

## Project Structure

```
frontend/
├── pages/
│   ├── _app.tsx                  # App wrapper, Layout, Toaster
│   ├── index.tsx                 # Dashboard
│   └── stocks/[ticker].tsx       # Stock detail
├── components/
│   ├── Layout.tsx                # Nav header, footer, live dot
│   ├── SignalsTable.tsx          # Sortable signals table
│   ├── GammaRadar.tsx            # Top gamma exposure widget
│   ├── DarkPoolFeed.tsx          # Top dark pool flows widget
│   ├── OptionsFlowTape.tsx       # Top options premiums widget
│   ├── AIBreakoutSignals.tsx     # AI predictions widget
│   ├── ScoreGauge.tsx            # Circular score visualizer
│   └── StockChart.tsx            # Candlestick price chart
├── lib/
│   ├── api.ts                    # Axios client, fetch functions, formatters
│   └── types.ts                  # TypeScript interfaces (mirror backend Pydantic models)
├── styles/
│   └── globals.css               # CSS variables, dark theme, utility classes
├── .env.local                    # NEXT_PUBLIC_API_URL
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

---

## Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Next.js | 14.1.4 | Framework (Pages Router) |
| React | 18 | UI |
| TypeScript | — | Type safety |
| Tailwind CSS | 3.4 | Styling |
| SWR | 2.2 | Data fetching + caching |
| Axios | 1.6 | HTTP client |
| Recharts | 2.12 | Charts (bar, area, radar) |
| lightweight-charts | 4.1 | Candlestick price chart |
| lucide-react | 0.356 | Icons |
| react-hot-toast | 2.4 | Notifications |

---

## Theming

Dark theme defined via CSS variables in `globals.css`:

| Variable | Value | Usage |
|----------|-------|-------|
| `--bg` | `#080c14` | Page background |
| `--surface` | `#0f1623` | Nav, panels |
| `--card` | `#141c2e` | Cards (`.glass-card`) |
| `--border` | `#1e2d45` | Borders, dividers |
| `--bull` | `#00d084` | Bullish / positive |
| `--bear` | `#ff4d6d` | Bearish / negative |
| `--accent` | `#3b82f6` | Links, active states |
| `--text` | `#e2e8f0` | Body text |
| `--muted` | `#64748b` | Secondary text |

Font: JetBrains Mono (monospace) loaded from Google Fonts.

---

## Connecting to AWS Backend

Update `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://mh3ytbcc9w.us-east-1.awsapprunner.com
```

Then restart the dev server or rebuild:
```bash
npm run dev
# or for production
npm run build && npm start
```
