export interface SignalResponse {
  ticker: string
  score: number
  breakout_probability: number
  dark_pool_flow: number
  signal: 'bullish' | 'bearish' | 'neutral'
  options_flow_score: number
  gamma_score: number
  volume_spike_score: number
  insider_score: number
  institutional_score: number
  price: number
  change_pct: number
  market_cap: number
}

export interface MarketData {
  ticker: string
  price: number
  change_pct: number
  volume: number
  avg_volume_30d: number
  volume_ratio: number
  market_cap: number
  short_interest: number
  high_52w: number
  low_52w: number
}

export interface OptionsFlowSignal {
  ticker: string
  premium: number
  strike: number
  expiration: string
  direction: string
  volume: number
  open_interest: number
  volume_oi_ratio: number
  option_type: string
  timestamp: string
  score: number
}

export interface DarkPoolSignal {
  ticker: string
  buy_volume: number
  sell_volume: number
  dark_pool_net_flow: number
  price: number
  timestamp: string
  score: number
}

export interface GammaExposureSignal {
  ticker: string
  gamma_exposure: number
  spot_price: number
  dealer_delta: number
  gamma_flip_level: number
  interpretation: string
  timestamp: string
  score: number
}

export interface InsiderTrade {
  ticker: string
  insider_name: string
  role: string
  transaction_type: string
  transaction_value: number
  shares: number
  price_per_share: number
  filing_date: string
  score: number
}

export interface AISignal {
  ticker: string
  breakout_probability: number
  confidence: number
  features_used: string[]
  model_version: string
  timestamp: string
}

export interface MasterSignal {
  ticker: string
  master_score: number
  signal_strength: string
  direction: string
  breakout_probability: number
  options_flow_score: number
  gamma_exposure_score: number
  dark_pool_score: number
  volume_spike_score: number
  insider_buying_score: number
  institutional_flow_score: number
  ai_score: number
  market_data: MarketData
  top_options_flow: OptionsFlowSignal | null
  dark_pool: DarkPoolSignal | null
  gamma: GammaExposureSignal | null
  insider_trades: InsiderTrade[]
  timestamp: string
}

export interface PricePoint {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface StockDetailResponse {
  ticker: string
  market_data: MarketData
  master_signal: MasterSignal
  price_history: PricePoint[]
  options_flow_history: OptionsFlowSignal[]
  dark_pool_history: DarkPoolSignal[]
  gamma_history: GammaExposureSignal[]
  insider_trades: InsiderTrade[]
  ai_signal: AISignal
}
