from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SignalStrength(str, Enum):
    WEAK = "weak"
    ACCUMULATION = "accumulation"
    STRONG_POSITIONING = "strong_positioning"
    EXPLOSIVE = "explosive"


class SignalDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class OptionsFlowSignal(BaseModel):
    ticker: str
    premium: float
    strike: float
    expiration: str
    direction: SignalDirection
    volume: int
    open_interest: int
    volume_oi_ratio: float
    option_type: str  # call / put
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    score: float = 0.0


class DarkPoolSignal(BaseModel):
    ticker: str
    buy_volume: float
    sell_volume: float
    dark_pool_net_flow: float
    price: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    score: float = 0.0


class GammaExposureSignal(BaseModel):
    ticker: str
    gamma_exposure: float
    spot_price: float
    dealer_delta: float
    gamma_flip_level: float
    interpretation: str  # volatility suppression / expansion
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    score: float = 0.0


class InsiderTrade(BaseModel):
    ticker: str
    insider_name: str
    role: str
    transaction_type: str  # buy / sell
    transaction_value: float
    shares: int
    price_per_share: float
    filing_date: str
    score: float = 0.0


class InstitutionalFlowSignal(BaseModel):
    ticker: str
    block_trade_volume: float
    etf_inflow: float
    etf_outflow: float
    net_etf_flow: float
    large_buyer_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    score: float = 0.0


class MarketData(BaseModel):
    ticker: str
    price: float
    change_pct: float
    volume: int
    avg_volume_30d: int
    volume_ratio: float
    market_cap: float
    short_interest: float
    high_52w: float
    low_52w: float


class AISignal(BaseModel):
    ticker: str
    breakout_probability: float
    confidence: float
    features_used: List[str]
    model_version: str = "xgb_v1"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MasterSignal(BaseModel):
    ticker: str
    master_score: float
    signal_strength: SignalStrength
    direction: SignalDirection
    breakout_probability: float
    options_flow_score: float
    gamma_exposure_score: float
    dark_pool_score: float
    volume_spike_score: float
    insider_buying_score: float
    institutional_flow_score: float
    ai_score: float
    market_data: MarketData
    top_options_flow: Optional[OptionsFlowSignal] = None
    dark_pool: Optional[DarkPoolSignal] = None
    gamma: Optional[GammaExposureSignal] = None
    insider_trades: List[InsiderTrade] = []
    institutional: Optional[InstitutionalFlowSignal] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def signal_label(self) -> str:
        if self.master_score >= 85:
            return "explosive"
        elif self.master_score >= 70:
            return "strong_positioning"
        elif self.master_score >= 40:
            return "accumulation"
        return "weak"


class AlertPayload(BaseModel):
    ticker: str
    master_score: float
    breakout_probability: float
    signal: str
    dark_pool_flow: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SignalResponse(BaseModel):
    ticker: str
    score: float
    breakout_probability: float
    dark_pool_flow: float
    signal: str
    options_flow_score: float
    gamma_score: float
    volume_spike_score: float
    insider_score: float
    institutional_score: float
    price: float
    change_pct: float
    market_cap: float


class PricePoint(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockDetailResponse(BaseModel):
    ticker: str
    market_data: MarketData
    master_signal: MasterSignal
    price_history: List[PricePoint]
    options_flow_history: List[OptionsFlowSignal]
    dark_pool_history: List[DarkPoolSignal]
    gamma_history: List[GammaExposureSignal]
    insider_trades: List[InsiderTrade]
    ai_signal: AISignal
