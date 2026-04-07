from __future__ import annotations

import math


def detect_invoice_anomalies(values: list[float]) -> dict[str, int]:
    vals = [float(v or 0) for v in values]
    if len(vals) < 4:
        return {"anomaly_count": 0}

    try:
        from sklearn.ensemble import IsolationForest  # type: ignore
        import numpy as np  # type: ignore

        X = np.array(vals).reshape(-1, 1)
        iso = IsolationForest(contamination=0.1, random_state=42)
        preds = iso.fit_predict(X)
        count = int((preds == -1).sum())
        return {"anomaly_count": count}
    except Exception:
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / max(1, len(vals) - 1)
        std = math.sqrt(var) if var > 0 else 0
        if std == 0:
            return {"anomaly_count": 0}
        count = sum(1 for v in vals if abs((v - mean) / std) > 2.5)
        return {"anomaly_count": count}

