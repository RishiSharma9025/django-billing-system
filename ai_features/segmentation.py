from __future__ import annotations

from collections import defaultdict


def segment_customers(rows: list[dict]) -> dict[str, int]:
    """
    rows: [{'name': 'x', 'total_paid': 123.0}, ...]
    """
    paid = [float(r.get("total_paid") or 0) for r in rows]
    if not paid:
        return {"high_value": 0, "mid_value": 0, "low_value": 0}

    try:
        from sklearn.cluster import KMeans  # type: ignore
        import numpy as np  # type: ignore

        X = np.array(paid).reshape(-1, 1)
        n_clusters = 3 if len(paid) >= 3 else len(paid)
        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        labels = km.fit_predict(X)
        centers = km.cluster_centers_.flatten().tolist()
        sorted_cluster_ids = sorted(range(len(centers)), key=lambda i: centers[i])
        cluster_names = {}
        if sorted_cluster_ids:
            cluster_names[sorted_cluster_ids[0]] = "low_value"
        if len(sorted_cluster_ids) > 1:
            cluster_names[sorted_cluster_ids[-1]] = "high_value"
        for cid in sorted_cluster_ids[1:-1]:
            cluster_names[cid] = "mid_value"

        counts = defaultdict(int)
        for cid in labels:
            counts[cluster_names.get(int(cid), "mid_value")] += 1
        return {
            "high_value": counts["high_value"],
            "mid_value": counts["mid_value"],
            "low_value": counts["low_value"],
        }
    except Exception:
        # Fallback quantile bins.
        ordered = sorted(paid)
        q1 = ordered[max(0, len(ordered) // 3 - 1)]
        q2 = ordered[max(0, (2 * len(ordered)) // 3 - 1)]
        counts = {"high_value": 0, "mid_value": 0, "low_value": 0}
        for val in paid:
            if val >= q2:
                counts["high_value"] += 1
            elif val <= q1:
                counts["low_value"] += 1
            else:
                counts["mid_value"] += 1
        return counts

