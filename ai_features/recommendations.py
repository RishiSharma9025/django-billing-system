from __future__ import annotations

from collections import Counter, defaultdict


def recommend_products(invoice_items: list[tuple[int, str]], top_n: int = 5) -> list[str]:
    """
    invoice_items: [(invoice_id, product_name), ...]
    Returns frequently co-occurring product recommendations.
    """
    by_invoice: dict[int, set[str]] = defaultdict(set)
    for inv_id, product_name in invoice_items:
        if product_name:
            by_invoice[int(inv_id)].add(product_name)

    pair_counts: Counter[str] = Counter()
    for products in by_invoice.values():
        plist = sorted(products)
        for i in range(len(plist)):
            for j in range(i + 1, len(plist)):
                pair_counts[f"{plist[i]} + {plist[j]}"] += 1

    return [p for p, _ in pair_counts.most_common(top_n)]

