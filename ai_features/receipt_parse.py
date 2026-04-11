from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional


def _to_decimal(s: str) -> Optional[Decimal]:
    s = re.sub(r"[^\d.]", "", s.replace(",", ""))
    if not s:
        return None
    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def parse_receipt_structured(text: str) -> Dict[str, Any]:
    """
    Heuristic extraction of total and line items from OCR text.

    Tuned for common English/Indian receipt wording.
    Returns:
      - total: string (or "")
      - items: list of {name, quantity, unit_price, line_total}
      - confidence: "heuristic"
    """
    text = (text or "").strip()
    out: Dict[str, Any] = {"total": None, "items": [], "confidence": "heuristic"}

    if not text:
        return out

    total: Optional[Decimal] = None
    total_patterns = [
        r"(?:grand\s*total|net\s*total|amount\s*payable|total\s*(?:due|payable)?|balance\s*due)\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+\.?\d*)",
        r"\btotal\b\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+\.?\d*)\s*$",
        r"paid[:\s]+[₹Rs.]?\s*([\d,]+\.?\d*)",
    ]
    for pat in total_patterns:
        for m in re.finditer(pat, text, re.I | re.MULTILINE):
            d = _to_decimal(m.group(1))
            if d is not None and (total is None or d >= total):
                total = d

    out["total"] = str(total) if total is not None else ""

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    items: List[Dict[str, Any]] = []
    seen = set()

    # Pattern: name ... qty x unit = line_total
    rx_mul = re.compile(
        r"^(.{2,60}?)\s+(\d+)\s*[x×]\s*([\d,]+\.?\d*)\s*=\s*([\d,]+\.?\d*)\s*$",
        re.I,
    )
    # Pattern: name qty amount (columns)
    rx_cols = re.compile(r"^(.{2,55}?)\s{2,}(\d+)\s+([\d,]+\.?\d*)\s*$")
    # Pattern trailing qty and money: Item name qty amt
    rx_tail = re.compile(r"^(.+?)\s+(\d+)\s+([\d,]+\.?\d*)\s*$")

    skip_kw = re.compile(
        r"^\s*(total|sub|tax|gst|date|invoice|bill|thank|cashier|amount|qty|rate|item)\b",
        re.I,
    )

    for ln in lines:
        if skip_kw.search(ln):
            continue
        if len(ln) < 4:
            continue

        m = rx_mul.match(ln)
        if m:
            name = m.group(1).strip(" -·\t")
            qty = int(m.group(2))
            unit = _to_decimal(m.group(3)) or Decimal("0")
            line_tot = _to_decimal(m.group(4)) or Decimal("0")
            key = (name.lower(), qty, str(line_tot))
            if key not in seen:
                seen.add(key)
                items.append(
                    {
                        "name": name[:200],
                        "quantity": qty,
                        "unit_price": str(unit),
                        "line_total": str(line_tot),
                    }
                )
            continue

        m = rx_cols.match(ln)
        if m:
            name = m.group(1).strip(" -·\t")
            qty = int(m.group(2))
            amt = _to_decimal(m.group(3)) or Decimal("0")
            if qty <= 0:
                continue
            unit = (amt / Decimal(qty)).quantize(Decimal("0.01"))
            key = (name.lower(), qty, str(amt))
            if key not in seen:
                seen.add(key)
                items.append(
                    {
                        "name": name[:200],
                        "quantity": qty,
                        "unit_price": str(unit),
                        "line_total": str(amt),
                    }
                )
            continue

        m = rx_tail.match(ln)
        if m and not re.search(r"[x×=]", ln):
            name = m.group(1).strip(" -·\t")
            # Reduce false positives: short names are more likely to be line items.
            if len(name.split()) > 1 or len(name) > 12:
                continue
            qty = int(m.group(2))
            amt = _to_decimal(m.group(3)) or Decimal("0")
            if qty <= 0 or amt <= 0:
                continue
            unit = (amt / Decimal(qty)).quantize(Decimal("0.01"))
            key = (name.lower(), qty, str(amt))
            if key not in seen and len(items) < 40:
                seen.add(key)
                items.append(
                    {
                        "name": name[:200],
                        "quantity": qty,
                        "unit_price": str(unit),
                        "line_total": str(amt),
                    }
                )

    out["items"] = items[:30]
    return out

