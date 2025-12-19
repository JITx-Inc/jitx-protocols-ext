# resistor_rules.py
from __future__ import annotations

"""
Resistor Rules: E-series validation + optional package power validation.

Purpose
-------
This module provides a single, ergonomic checking function:

    check_resistor(...)

It enforces:
  1) Resistance value is a standard E-series value (default: E96)
  2) Optional power dissipation check using P = I^2 * R, based on package size

Key Defaults (Design Intent)
----------------------------
- E-series: E96 (1%) is enforced ALWAYS.
- Non-standard value: ERROR by default.
  - You can downgrade non-standard value to WARNING via:
        allow_nonstandard_warning=True

- Power check: OPTIONAL.
  - If current_amps is omitted (None), power check is skipped.
  - If current_amps is provided (including 0.0), power check runs.

Severity / ok rules
-------------------
Return severity is one of: "ok" | "warning" | "error".

- If E96 matches: E-series contributes "ok".
- If E96 does not match:
    - allow_nonstandard_warning=False -> contributes "error"
    - allow_nonstandard_warning=True  -> contributes "warning" (and overall ok can still be True)

- If power check runs and fails -> contributes "error" and overall ok becomes False.

Return Object Schema (ResistorRuleResult)
-----------------------------------------
check_resistor(...) returns ResistorRuleResult with fields:

- ok: bool
    True if all enforced rules pass.
    Note: if allow_nonstandard_warning=True, a nonstandard value does not force ok=False.

- severity: str
    "ok" | "warning" | "error"
    "warning" typically means only the E-series mismatch is present and was downgraded.

- summary: str
    Single-line status summary designed for logs.

- issues: List[str]
    Human-readable messages. Includes an INFO line when power check is skipped.

- eseries: ESeriesResult
    Result of E-series validation. (Always present.)

- power: Optional[ResistorPowerResult]
    None if current_amps was not provided; otherwise a full power result.

Typical Patterns
----------------
1) Enforce E96 only (power skipped)
2) Enforce E96 + power (when current known)
3) Allow nonstandard as WARNING (but still enforce power if provided)
4) Use tighter/looser power derating and design margin

Examples (copy/paste)
---------------------
Example A: E96-only check (no current provided -> power skipped)
    r = check_resistor(size="0603", resistance_ohms=49.9)
    # Expected:
    #   r.power is None
    #   r.eseries.ok is True
    #   r.ok is True
    #   r.severity == "ok"

Example B: Nonstandard value is ERROR by default
    r = check_resistor(size="0603", resistance_ohms=47.5)
    # Expected:
    #   r.ok is False
    #   r.severity == "error"
    #   r.power is None (since no current)
    #   r.eseries.ok is False

Example C: Downgrade nonstandard to WARNING
    r = check_resistor(size="0603", resistance_ohms=47.5, allow_nonstandard_warning=True)
    # Expected:
    #   r.ok is True  (because nonstandard is allowed as warning)
    #   r.severity == "warning"
    #   r.power is None (since no current)

Example D: Enable power check by supplying current_amps
    r = check_resistor(size="0603", resistance_ohms=49.9, current_amps=0.08)
    # Expected:
    #   r.power is not None
    #   r.ok depends on I^2*R vs allowed package power

Example E: Power failure dominates (always error)
    r = check_resistor(size="0603", resistance_ohms=10.0, current_amps=0.25)
    # P = 0.25^2 * 10 = 0.625 W -> likely fails for small packages
    # Expected:
    #   r.ok is False
    #   r.severity == "error"
    #   r.power.ok is False

Example F: Explicitly run power check with current_amps=0.0
    r = check_resistor(size="0603", resistance_ohms=49.9, current_amps=0.0)
    # Expected:
    #   r.power is not None
    #   r.power.power_dissipated_w == 0.0
    #   r.ok is True (assuming E96 passes)

Notes
-----
- Size parsing and package power ratings are handled in resistor_power_check.py.
  If you pass ambiguous sizes like "0402"/"0603", that module may default to imperial,
  and also supports explicit prefixes like "I0402" or "M1005" for clarity.
"""

from dataclasses import dataclass
from typing import List, Optional

from resistor_power_check import check_resistor_power, ResistorPowerResult
from eseries_check import check_eseries_value, ESeriesResult


@dataclass(frozen=True)
class ResistorRuleResult:
    ok: bool
    severity: str  # "ok" | "warning" | "error"
    issues: List[str]
    summary: str
    power: Optional[ResistorPowerResult]
    eseries: ESeriesResult


def check_resistor(
    *,
    size: str,
    resistance_ohms: float,
    current_amps: Optional[float] = None,
    derating_factor: float = 0.8,
    design_margin: float = 2.0,
    allow_nonstandard_warning: bool = False,
) -> ResistorRuleResult:
    """
    Validate a resistor selection against:
      - E96 preferred value series (always checked)
      - Package power handling (optional; checked only if current_amps is provided)

    Parameters
    ----------
    size:
        Resistor package size string. Common: "0603", "0805", etc.
        Power sizing behavior depends on resistor_power_check._normalize_size().

    resistance_ohms:
        Resistance in ohms. Must be > 0.

    current_amps:
        If provided, power check runs using P = I^2 * R.
        If omitted (None), power check is skipped.

    derating_factor:
        Applies only if power check runs.
        Example: 0.7 or 0.8 for elevated temperature / limited copper / airflow.

    design_margin:
        Applies only if power check runs.
        Example: 2.0 means "use <= 50% of derated rated power".

    allow_nonstandard_warning:
        If False (default), non-E96 values are an ERROR and make ok=False.
        If True, non-E96 values are a WARNING and do not force ok=False.

    Returns
    -------
    ResistorRuleResult:
        - ok: bool
        - severity: "ok" | "warning" | "error"
        - summary: single-line
        - issues: list of messages (includes INFO when power is skipped)
        - eseries: ESeriesResult (always present)
        - power: Optional[ResistorPowerResult] (None if power skipped)

    Quick Expectations
    ------------------
    - If current_amps is None: power=None and an INFO line is added to issues.
    - If allow_nonstandard_warning is False: E-series mismatch => ok=False.
    - If allow_nonstandard_warning is True: E-series mismatch => severity "warning" and ok can be True.
    """
    issues: List[str] = []

    # E-series check (always)
    es = check_eseries_value(
        resistance_ohms,
        series="E96",
        allow_warning=allow_nonstandard_warning,
    )
    if not es.ok:
        issues.append(es.message)

    # Optional power check
    power: Optional[ResistorPowerResult] = None
    if current_amps is None:
        issues.append(
            "[RULE][INFO] Power check skipped: current_amps not provided. "
            "Provide current_amps=<A> to enable package power validation."
        )
    else:
        power = check_resistor_power(
            size=size,
            resistance_ohms=resistance_ohms,
            current_amps=current_amps,
            derating_factor=derating_factor,
            design_margin=design_margin,
        )
        if not power.ok:
            issues.append(power.message)

    # Compute overall ok/severity
    ok = es.ok or allow_nonstandard_warning

    severity = "ok"
    if es.severity == "warning":
        severity = "warning"
    if es.severity == "error":
        severity = "error"

    if power is not None:
        ok = ok and power.ok
        if not power.ok:
            severity = "error"

    # Summary string
    power_state = "checked" if power is not None else "skipped"
    summary = (
        f"[RULE][{severity.upper()}] size={size}, R={resistance_ohms:g} Ω, "
        f"E96={es.severity.upper()}, power={power_state}."
    )

    return ResistorRuleResult(
        ok=ok,
        severity=severity,
        issues=issues,
        summary=summary,
        power=power,
        eseries=es,
    )