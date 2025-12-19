# resistor_power_check.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ResistorPowerResult:
    ok: bool
    severity: str  # "ok" | "error"
    size: str      # canonical, like "I0603" or "M1608"
    resistance_ohms: float
    current_amps: float
    power_dissipated_w: float
    allowed_power_w: float
    margin: float
    message: str


# Canonical keys:
#   I#####: imperial (01005 is 5 digits)
#   I#### : imperial (e.g. I0402)
#   M#### : metric 4-digit code (e.g. M1608)
#
# Values are nominal power ratings from your table.
RESISTOR_POWER_W: Mapping[str, float] = {
    # Imperial -> power
    "I01005": 0.031,
    "I0201":  0.05,
    "I0402":  0.062,
    "I0603":  0.10,
    "I0805":  0.125,
    "I1206":  0.25,
    "I1210":  0.5,
    "I1812":  0.75,
    "I2010":  0.75,
    "I2512":  1.0,

    # Metric -> power (same rows, metric equivalents)
    "M0402":  0.031,
    "M0603":  0.05,
    "M1005":  0.062,
    "M1608":  0.10,
    "M2012":  0.125,
    "M3216":  0.25,
    "M3225":  0.5,
    "M4532":  0.75,
    "M5025":  0.75,
    "M6332":  1.0,
}


_IMPERIAL_SET = {"01005", "0201", "0402", "0603", "0805", "1206", "1210", "1812", "2010", "2512"}
_METRIC_SET   = {"0402", "0603", "1005", "1608", "2012", "3216", "3225", "4532", "5025", "6332"}


def _digits_only(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def _normalize_size(size: str) -> str:
    """
    Produces a canonical size key: 'I0402', 'M1608', etc.

    Rules:
      - If prefixed with 'I' or 'M', respect it: 'I0402', 'M1005'
      - Otherwise, if ambiguous (0402, 0603), DEFAULT TO IMPERIAL
        because this project is using imperial sizing.
      - Otherwise infer by membership in known imperial/metric sets.
    """
    raw = size.strip().upper().replace(" ", "").replace("-", "").replace("_", "")

    # Explicit prefix support: I0402, M1608, etc.
    if raw.startswith("I"):
        d = _digits_only(raw[1:])
        return "I" + d
    if raw.startswith("M"):
        d = _digits_only(raw[1:])
        return "M" + d

    d = _digits_only(raw)

    # Ambiguous codes default to imperial (your stated intent)
    if d in ("0402", "0603"):
        return "I" + d

    if d in _IMPERIAL_SET:
        return "I" + d
    if d in _METRIC_SET:
        return "M" + d

    # If we can't classify, return something that will fail lookup clearly
    return d


def check_resistor_power(
    size: str,
    resistance_ohms: float,
    current_amps: float,
    *,
    derating_factor: float = 1.0,
    design_margin: float = 1.0,
) -> ResistorPowerResult:
    if resistance_ohms <= 0:
        raise ValueError("[POWER] resistance_ohms must be > 0")
    if current_amps < 0:
        raise ValueError("[POWER] current_amps must be >= 0")
    if derating_factor <= 0:
        raise ValueError("[POWER] derating_factor must be > 0")
    if design_margin <= 0:
        raise ValueError("[POWER] design_margin must be > 0")

    key = _normalize_size(size)
    if key not in RESISTOR_POWER_W:
        known = ", ".join(sorted(RESISTOR_POWER_W.keys()))
        raise KeyError(
            f"[POWER] Unknown/unsupported resistor size '{size}' (normalized '{key}'). "
            f"Tip: use 'I0402' for imperial 0402, or 'M1005' for metric 1005. "
            f"Known keys: {known}"
        )

    power_dissipated = (current_amps * current_amps) * resistance_ohms
    nominal_power = float(RESISTOR_POWER_W[key])
    allowed_power = (nominal_power * derating_factor) / design_margin

    ok = power_dissipated <= allowed_power
    severity = "ok" if ok else "error"
    margin = float("inf") if power_dissipated == 0 else (allowed_power / power_dissipated)

    if ok:
        msg = (
            f"[POWER][OK] {key}: I={current_amps:g} A, R={resistance_ohms:g} Ω → "
            f"P={power_dissipated:g} W ≤ allowed={allowed_power:g} W "
            f"(nominal={nominal_power:g} W, derating={derating_factor:g}, margin={design_margin:g}, "
            f"headroom={margin:.3g}×)"
        )
    else:
        msg = (
            f"[POWER][ERROR] {key}: I={current_amps:g} A, R={resistance_ohms:g} Ω → "
            f"P={power_dissipated:g} W > allowed={allowed_power:g} W "
            f"(nominal={nominal_power:g} W, derating={derating_factor:g}, margin={design_margin:g}). "
            f"Action: reduce I, reduce R, use larger package, or split across multiple resistors."
        )

    return ResistorPowerResult(
        ok=ok,
        severity=severity,
        size=key,
        resistance_ohms=float(resistance_ohms),
        current_amps=float(current_amps),
        power_dissipated_w=float(power_dissipated),
        allowed_power_w=float(allowed_power),
        margin=float(margin),
        message=msg,
    )