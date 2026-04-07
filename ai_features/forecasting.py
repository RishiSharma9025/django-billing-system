from __future__ import annotations

from typing import Iterable


def forecast_revenue(monthly_values: Iterable[float], periods: int = 3) -> list[float]:
    values = [float(v or 0) for v in monthly_values]
    if not values:
        return [0.0] * periods
    if len(values) == 1:
        return [values[0]] * periods

    try:
        from sklearn.linear_model import LinearRegression  # type: ignore
        import numpy as np  # type: ignore

        x = np.arange(len(values)).reshape(-1, 1)
        y = np.array(values)
        model = LinearRegression()
        model.fit(x, y)
        future_x = np.arange(len(values), len(values) + periods).reshape(-1, 1)
        preds = model.predict(future_x)
        return [max(0.0, float(p)) for p in preds]
    except Exception:
        # Lightweight fallback if sklearn/numpy unavailable.
        diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
        avg_diff = sum(diffs) / len(diffs) if diffs else 0.0
        out = []
        curr = values[-1]
        for _ in range(periods):
            curr = max(0.0, curr + avg_diff)
            out.append(curr)
        return out

