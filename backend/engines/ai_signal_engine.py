"""
AI Signal Engine
XGBoost classifier trained on synthetic smart-money features.

Input features:
  options_flow_score, dark_pool_net_flow, gamma_exposure,
  short_interest, volume_ratio, insider_buying_flag

Output:
  breakout_probability (0.0 – 1.0)
"""
import numpy as np
import random
from datetime import datetime
from typing import List, Tuple
from models.signals import AISignal

try:
    import xgboost as xgb
    from sklearn.preprocessing import StandardScaler
    _XGB_AVAILABLE = True
except ImportError:
    _XGB_AVAILABLE = False

_FEATURE_NAMES = [
    "options_flow_score",
    "dark_pool_net_flow_normalized",
    "gamma_exposure_normalized",
    "short_interest",
    "volume_ratio",
    "insider_buying_flag",
]

_model = None
_scaler = None


def _generate_training_data(n: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
    """Synthesize labeled training data from signal distributions."""
    rng = np.random.RandomState(42)

    options_flow = rng.uniform(0, 100, n)
    dark_pool = rng.uniform(-1, 1, n)           # normalized [-1, 1]
    gamma_exp = rng.uniform(-1, 1, n)           # normalized [-1, 1]
    short_interest = rng.uniform(0.01, 0.50, n)
    volume_ratio = rng.uniform(0.5, 6.0, n)
    insider_flag = rng.choice([0, 1], n, p=[0.75, 0.25])

    # Ground-truth breakout label: combination of signal strengths
    score = (
        options_flow * 0.30 +
        np.clip(dark_pool, 0, 1) * 30 +
        np.clip(gamma_exp, 0, 1) * 20 +
        (volume_ratio - 1) * 8 +
        insider_flag * 15
    )
    noise = rng.normal(0, 5, n)
    prob = 1 / (1 + np.exp(-(score + noise - 40) / 15))
    labels = (prob > 0.5).astype(int)

    X = np.column_stack([options_flow, dark_pool, gamma_exp, short_interest, volume_ratio, insider_flag])
    return X, labels


def _train_model():
    global _model, _scaler
    if not _XGB_AVAILABLE:
        return

    X, y = _generate_training_data()
    from sklearn.preprocessing import StandardScaler
    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)

    _model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        verbosity=0,
    )
    _model.fit(X_scaled, y)


def _fallback_score(options_score: float, dark_pool_normalized: float, gamma_normalized: float,
                    short_interest: float, volume_ratio: float, insider_flag: int) -> float:
    """Simple heuristic when XGBoost is unavailable."""
    raw = (
        options_score * 0.30 +
        max(0, dark_pool_normalized) * 30 +
        max(0, gamma_normalized) * 20 +
        (volume_ratio - 1) * 8 +
        insider_flag * 15
    )
    return round(min(1.0, max(0.0, raw / 100)), 4)


def get_ai_signal(
    ticker: str,
    options_flow_score: float,
    dark_pool_net_flow: float,
    gamma_exposure: float,
    short_interest: float,
    volume_ratio: float,
    insider_buying_flag: int,
) -> AISignal:
    global _model, _scaler

    if _model is None and _XGB_AVAILABLE:
        _train_model()

    # Normalize continuous features
    dark_pool_norm = np.clip(dark_pool_net_flow / 50_000_000, -1.0, 1.0)
    gamma_norm = np.clip(gamma_exposure / 500_000_000, -1.0, 1.0)

    if _model is not None and _scaler is not None:
        X = np.array([[options_flow_score, dark_pool_norm, gamma_norm,
                       short_interest, volume_ratio, insider_buying_flag]])
        X_scaled = _scaler.transform(X)
        prob = float(_model.predict_proba(X_scaled)[0][1])
        confidence = float(max(_model.predict_proba(X_scaled)[0]))
    else:
        prob = _fallback_score(options_flow_score, dark_pool_norm, gamma_norm,
                               short_interest, volume_ratio, insider_buying_flag)
        confidence = 0.65

    return AISignal(
        ticker=ticker,
        breakout_probability=round(prob, 4),
        confidence=round(confidence, 4),
        features_used=_FEATURE_NAMES,
        model_version="xgb_v1" if _XGB_AVAILABLE else "heuristic_v1",
        timestamp=datetime.utcnow(),
    )


# Train on module load (non-blocking in production this would be async or pre-trained)
if _XGB_AVAILABLE:
    try:
        _train_model()
    except Exception:
        pass
