# eseries_check.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class ESeriesResult:
    ok: bool
    severity: str  # "ok" | "warning" | "error"
    value_ohms: float
    series: str
    nearest_standard_ohms: float
    rel_error: float
    message: str


def _sigfig_round(x: float, sigfigs: int) -> float:
    if x == 0:
        return 0.0
    exp = int(math.floor(math.log10(abs(x))))
    places = sigfigs - 1 - exp
    return round(x, places)


def _fallback_nearest(value_ohms: float, series: str) -> float:
    s = series.upper().lstrip("E")
    n = int(s)
    sigfigs = 2 if n <= 24 else 3

    decade = int(math.floor(math.log10(value_ohms)))
    mantissa = value_ohms / (10 ** decade)
    if mantissa < 1:
        mantissa *= 10
        decade -= 1

    bases = []
    for k in range(n):
        bases.append(_sigfig_round(10 ** (k / n), sigfigs))
    bases.append(10.0)

    nearest = min(bases, key=lambda b: abs(b - mantissa))
    if nearest >= 9.999:
        return 1.0 * (10 ** (decade + 1))
    return nearest * (10 ** decade)


def _try_eseries_nearest(value_ohms: float, series: str) -> Optional[float]:
    try:
        import eseries  # type: ignore
    except Exception:
        return None

    s = series.upper()

    # Try common API shapes defensively
    try:
        obj = getattr(eseries, s)
        if hasattr(obj, "nearest"):
            return float(obj.nearest(value_ohms))
    except Exception:
        pass

    try:
        if hasattr(eseries, "nearest"):
            return float(eseries.nearest(value_ohms, s))
    except Exception:
        pass

    try:
        if hasattr(eseries, "ESeries"):
            ser = eseries.ESeries(s)
            if hasattr(ser, "nearest"):
                return float(ser.nearest(value_ohms))
    except Exception:
        pass

    return None


def check_eseries_value(
    value_ohms: float,
    *,
    series: str = "E96",
    allow_warning: bool = False,
) -> ESeriesResult:
    """
    Default: E96 (1%) enforcement.
    Non-standard values are ERROR by default; set allow_warning=True to downgrade.
    """
    if value_ohms <= 0:
        raise ValueError("[ESERIES] value_ohms must be > 0")

    series = series.strip().upper()
    nearest = _try_eseries_nearest(value_ohms, series)
    source = "eseries" if nearest is not None else "fallback"
    if nearest is None:
        nearest = _fallback_nearest(value_ohms, series)

    rel_error = abs(value_ohms - nearest) / nearest
    ok = rel_error == 0.0

    if ok:
        severity = "ok"
        msg = f"[ESERIES][OK] R={value_ohms:g} Ω is a standard {series} value."
    else:
        severity = "warning" if allow_warning else "error"
        msg = (
            f"[ESERIES][{severity.upper()}] R={value_ohms:g} Ω is not a standard {series} value. "
            f"Nearest {series} is {nearest:g} Ω (Δ={rel_error * 100:.3f}%, via {source}). "
            f"Action: change to {nearest:g} Ω, or set allow_nonstandard_warning=True to downgrade."
        )

    return ESeriesResult(
        ok=ok,
        severity=severity,
        value_ohms=float(value_ohms),
        series=series,
        nearest_standard_ohms=float(nearest),
        rel_error=float(rel_error),
        message=msg,
    )