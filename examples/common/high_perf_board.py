"""High-performance HDI board substrate.

Adapted from `JITx-Inc/chaos_hfss/bga-optimization/bga_optimization/substrate.py`
(https://github.com/JITx-Inc/chaos_hfss). The chaos_hfss original was an
8-layer single-shielded-layer-per-side stack tuned for one 85 Ω BGA-escape
experiment; this file scales it up to a 16-layer 3-shielded-routing-layer-
per-side stack for the LPDDR5 / DDR5 / GDDR7 examples and the XC2VE3858
FPGA's heavy routing density needs.

Stackup
-------
16 conductor layers, symmetric about a 0.8 mm core. One generic low-loss
dielectric throughout (Dk 3.0, tan δ 0.004), 0.5 oz copper on every layer.

Layer order (top to bottom)::

    0   L1_Signal1   - top surface signal / BGA escape (microstrip)
    1   L2_GPlane2   - GND reference above L3
    2   L3_Signal3   - inner stripline #1 (shielded)
    3   L4_GPlane4   - GND reference between L3 and L5
    4   L5_Signal5   - inner stripline #2 (shielded)
    5   L6_GPlane6   - GND reference between L5 and L7
    6   L7_Signal7   - inner stripline #3 (shielded)
    7   L8_GPlane8   - GND reference above d_center
        d_center     - 0.8 mm core (Symmetric mirror)
    -8  L9_GPlane8'  - GND reference below d_center
    -7  L10_Signal7' - mirrored inner stripline #3 (shielded)
    -6  L11_GPlane6' - GND reference
    -5  L12_Signal5' - mirrored inner stripline #2 (shielded)
    -4  L13_GPlane4' - GND reference
    -3  L14_Signal3' - mirrored inner stripline #1 (shielded)
    -2  L15_GPlane2' - GND reference below L14
    -1  L16_Signal1' - bottom surface signal (microstrip)

That's 6 shielded routing layers (L3, L5, L7 + their mirrors L10, L12, L14)
plus 2 microstrip surface layers. Total board thickness ≈ 2.5 mm.

Routing structures
------------------
- ``SE_50``           — 50 Ω single-ended stripline (LPDDR5 DQ/CA, DDR5 SE)
- ``SE_40``           — 40 Ω single-ended stripline (LPDDR5 per AMD UG863,
                          LPDDR4 DQ)
- ``DRS_DiffPair_75`` — 75 Ω differential stripline (LPDDR5 CK/WCK/RDQS
                          per AMD UG863)
- ``DRS_DiffPair_85`` — 85 Ω differential stripline (PCIe, USB3)
- ``DRS_DiffPair_90`` — 90 Ω differential stripline (USB2)
- ``DRS_DiffPair_100`` — 100 Ω differential stripline (legacy non-AMD-spec
                          LPDDR5; kept for backward compatibility)

Every routing structure spans all 6 shielded layers — the engine picks
which layer a given net traces on. **No diff structure has via fencing
in its default configuration**; see "Optional fence vias" below.

Vias
----
BGA escape (top-side)
    - ``uVia_L1_L3`` — L1 → L3 (shallowest stripline)
    - ``uVia_L1_L5`` — L1 → L5
    - ``uVia_L1_L7`` — L1 → L7 (deepest stripline before core)

Half-stack GND stitching
    - ``uStitch_L1_L8`` — every top-half GND plane (L1 ↔ L8)
    - ``uStitch_L9_L16`` — every bottom-half GND plane (L9 ↔ L16)

Mechanical through-hole
    - ``TH_Via`` — PTH components + top-to-bottom GND stitching
    - ``TH_Via_Pwr`` — via-in-pad variant for tight GND stitching

Optional fence vias (defined on the substrate but **not** in the default
``HighPerfBoard.vias`` list)
    - ``uFence_L2_L4``, ``uFence_L4_L6``, ``uFence_L6_L8`` — top half
    - ``uFence_L9_L11``, ``uFence_L11_L13``, ``uFence_L13_L15`` — bottom half

    LPDDR5 routing per AMD UG863 doesn't require fence vias; we keep them
    out of the default board to reduce plate-copper and via inventory.
    Subclass ``HighPerfSubstrate`` with custom routing structures that
    pass ``fences=_ALL_FENCES`` to :py:func:`_diff_layers_3psh`, plus
    extend ``HighPerfBoard.vias`` to include the relevant ``uFence_*``
    Via classes, if your channel (e.g. PCIe Gen 5+) needs fencing.

Trace-width disclaimer
----------------------
The trace widths and pair spacings in this file were estimated from
field-solver rules of thumb on this stackup; they have **not** been
verified by impedance simulation. They're realistic enough to satisfy
fab-rule and routing constraints in the example designs but should be
re-tuned for any production use.
"""

from __future__ import annotations

from jitx.board import Board
from jitx.constraints import ViaFencePattern
from jitx.container import inline
from jitx.layerindex import Side
from jitx.shapes.composites import rectangle
from jitx.shapes.shapely import ShapelyGeometry
from jitx.si import (
    DifferentialRoutingStructure,
    PinModel,
    RoutingStructure,
    symmetric_routing_layers,
)
from jitx.stackup import Conductor, Dielectric, Symmetric
from jitx.substrate import FabricationConstraints, Substrate
from jitx.units import ohm
from jitx.via import Via, ViaType
from jitxlib.physics import phase_velocity


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

_DIELECTRIC_THICKNESS = 0.1
_DIELECTRIC_COEFFICIENT = 3.0

class HighPerfDielectric(Dielectric):
    """Low-loss generic dielectric — Dk 3.0, tan δ 0.004."""

    dielectric_coefficient = _DIELECTRIC_COEFFICIENT
    loss_tangent = 0.004


class HighPerfSolderMask(Dielectric):
    """Generic soldermask — Dk 3.8, tan δ 0.02."""

    dielectric_coefficient = 3.8
    loss_tangent = 0.02


class HighPerfCopper(Conductor):
    """0.5 oz copper, moderate roughness (Rz ≈ 1 µm)."""

    roughness = 1.0


# Phase velocity used by all stripline layer entries (Dk 3.0).
_VEL_STRIPLINE = phase_velocity(_DIELECTRIC_COEFFICIENT)


# ---------------------------------------------------------------------------
# Stackup
# ---------------------------------------------------------------------------


class HighPerfStackup(Symmetric):
    """16-layer symmetric stackup, 0.1 mm dielectrics + 0.8 mm core.

    Defined as a :py:class:`Symmetric` stackup — only the top half is
    listed; JITX mirrors it about ``d_center``.

    Top-half layer order::

        L1  Signal1   - top signal / BGA escape (microstrip)
        L2  GPlane2   - GND ref above L3
        L3  Signal3   - inner stripline #1 (shielded by L2 + L4)
        L4  GPlane4   - GND ref between L3 and L5
        L5  Signal5   - inner stripline #2 (shielded by L4 + L6)
        L6  GPlane6   - GND ref between L5 and L7
        L7  Signal7   - inner stripline #3 (shielded by L6 + L8)
        L8  GPlane8   - GND ref above d_center
        d_center      - 0.8 mm core (mirror plane)

    The bottom half (L9..L16) mirrors L8..L1 in reverse — i.e. L9 = L8',
    L10 = L7', ..., L16 = L1'. This gives 6 shielded routing layers
    (L3, L5, L7 + their mirrors L14, L12, L10) plus 2 microstrip surface
    layers (L1, L16). Total board thickness ≈ 2.5 mm.
    """

    top_mask = HighPerfSolderMask(thickness=0.0127)

    L1_Signal1 = HighPerfCopper(thickness=0.0175, name="L1-Signal1")
    d_1_2 = HighPerfDielectric(thickness=_DIELECTRIC_THICKNESS)
    L2_GPlane2 = HighPerfCopper(thickness=0.0175, name="L2-GPlane2")
    d_2_3 = HighPerfDielectric(thickness=_DIELECTRIC_THICKNESS)
    L3_Signal3 = HighPerfCopper(thickness=0.0175, name="L3-Signal3")
    d_3_4 = HighPerfDielectric(thickness=_DIELECTRIC_THICKNESS)
    L4_GPlane4 = HighPerfCopper(thickness=0.0175, name="L4-GPlane4")
    d_4_5 = HighPerfDielectric(thickness=_DIELECTRIC_THICKNESS)
    L5_Signal5 = HighPerfCopper(thickness=0.0175, name="L5-Signal5")
    d_5_6 = HighPerfDielectric(thickness=_DIELECTRIC_THICKNESS)
    L6_GPlane6 = HighPerfCopper(thickness=0.0175, name="L6-GPlane6")
    d_6_7 = HighPerfDielectric(thickness=_DIELECTRIC_THICKNESS)
    L7_Signal7 = HighPerfCopper(thickness=0.0175, name="L7-Signal7")
    d_7_8 = HighPerfDielectric(thickness=_DIELECTRIC_THICKNESS)
    L8_GPlane8 = HighPerfCopper(thickness=0.0175, name="L8-GPlane8")

    # Center dielectric — thick core, full thickness mirrored below.
    d_center = HighPerfDielectric(thickness=0.8, name="Core")


# ---------------------------------------------------------------------------
# Fabrication constraints — HDI class
# ---------------------------------------------------------------------------


class HighPerfFabRules(FabricationConstraints):
    """HDI-class fab rules picked tight enough that diff-pair neckdown
    clearances aren't clamped up by the global rule and BGA fanout fits.
    """

    min_copper_width = 0.05
    min_copper_copper_space = 0.05
    min_copper_hole_space = 0.05
    min_copper_edge_space = 0.15
    min_annular_ring = 0.04
    min_drill_diameter = 0.05
    min_hole_to_hole = 0.3
    min_pitch_leaded = 0.2
    min_pitch_bga = 0.4
    max_board_width = 500
    max_board_height = 400
    min_silkscreen_width = 0.1
    min_silk_solder_mask_space = 0.05
    min_silkscreen_text_height = 0.6
    solder_mask_registration = 0.025
    min_soldermask_opening = 0.025
    min_soldermask_bridge = 0.04
    min_th_pad_expand_outer = 0.08
    min_pth_pin_solder_clearance = 0.0


# Design-rule tags previously defined here (DiffPairTag, GndReturnTag,
# BGAFanoutTag) have been removed — they were never assigned to any net,
# so the `dp_to_gnd` clearance rule that referenced them never fired.
# The signal-type tag library lives in
# `jitx_protocols_ext.protocols.memory.lpddr_constraints` instead.


# ---------------------------------------------------------------------------
# Routing-structure helpers
# ---------------------------------------------------------------------------
# Module-level so the routing structures inside `HighPerfSubstrate` can
# call them while passing in the substrate-specific fence Via classes.

#: Fence-pattern shared by every diff-pair routing structure that uses
#: via fencing. Pitch / offset tuned for adequate return-path
#: containment without choking the BGA fanout.
_FENCE = ViaFencePattern(pitch=0.5, offset=0.43, num_rows=1)


# ---------------------------------------------------------------------------
# Inner-stripline trace dimensions
# ---------------------------------------------------------------------------
# Public constants — single source of truth for the trace widths and
# diff-pair spacings used by both the layered routing structures below
# and the tag-based design-constraint rules generated by
# `lpddr_constraints.make_lpddr_routing_rules`. Caller-side imports
# should pull from here rather than from the routing structures, which
# are opaque structural objects.

INNER_SE_40_TRACE_WIDTH: float = 0.1405
"Inner-stripline SE 40 Ω trace width (mm). LPDDR5 DQ/DMI/CA/CSn per AMD UG863."

INNER_SE_40_NECK_DOWN_WIDTH: float = 0.0995
"Inner-stripline SE 50 Ω +/- 10% neckdown width (mm)."

INNER_SE_40_NECK_DOWN_CLEARANCE: float = 0.0762
"Inner-stripline SE 40 Ω +/- 10% neckdown width (mm)."

INNER_SE_50_TRACE_WIDTH: float = 0.0995
"Inner-stripline SE 50 Ω trace width (mm). DDR5 SE, legacy LPDDR5 DQ."

INNER_SE_50_NECK_DOWN_WIDTH: float = 0.080
"Inner-stripline SE 50 Ω neckdown width (mm)."

INNER_DIFF_75_TRACE_WIDTH: float = 0.110
"Inner-stripline 75 Ω diff trace width (mm). LPDDR5 CK/WCK/RDQS per AMD UG863."

INNER_DIFF_75_PAIR_SPACING: float = 0.08
"Inner-stripline 75 Ω diff pair spacing (mm)."

INNER_DIFF_85_TRACE_WIDTH: float = 0.10
"Inner-stripline 85 Ω diff trace width (mm). PCIe, USB3."

INNER_DIFF_85_PAIR_SPACING: float = 0.135
"Inner-stripline 85 Ω diff pair spacing (mm)."

INNER_DIFF_90_TRACE_WIDTH: float = 0.095
"Inner-stripline 90 Ω diff trace width (mm). USB2."

INNER_DIFF_90_PAIR_SPACING: float = 0.150
"Inner-stripline 90 Ω diff pair spacing (mm)."

INNER_DIFF_100_TRACE_WIDTH: float = 0.0762
"Inner-stripline 100 Ω diff trace width (mm). Legacy non-AMD-spec LPDDR5."

INNER_DIFF_100_PAIR_SPACING: float = 0.0762
"Inner-stripline 100 Ω diff pair spacing (mm)."


# ---------------------------------------------------------------------------
# AMD UG863 H-derived clearances
# ---------------------------------------------------------------------------
# H = distance from a signal layer to its nearest GND return plane. For
# the high-perf 16-layer stripline stackup this is the inner-stripline
# dielectric thickness (0.1 mm). Hard-coded here rather than introspected
# from the live stackup so the routing structures remain pure data — if
# you change the stackup dielectric, update this constant to match.
_H_STRIPLINE: float = _DIELECTRIC_THICKNESS

# UG863 "Outside SoC/DRAM" inter-net clearance multipliers in units of
# H (the strictest applicable rule defines the per-layer routing-
# structure clearance; tag-based rules in lpddr_constraints layer on
# the looser cross-class clearances).
_H_MUL_DATA_SAME_BYTE: float = 2.5  # DQ-to-DQ within byte
_H_MUL_DATA_STROBE_SAME_BYTE: float = 5.0  # DQ ↔ WCK/RDQS within byte
_H_MUL_INTER_BYTE: float = 7.0  # data/strobe across bytes
_H_MUL_CACK_TO_DATA: float = 7.0  # CAC/CK ↔ data/strobe
_H_MUL_CA_TO_CK: float = 5.0  # CA/CSn ↔ CK
_H_MUL_CAC_SAME: float = 2.5  # within CAC class
# UG863 "Under SoC/DRAM" tighter rules (used as neck-down clearances).
_H_MUL_NECK_DATA_SAME_BYTE: float = 1.0
_H_MUL_NECK_INTER_BYTE: float = 2.0


def _diff_layer(
    trace_width: float,
    pair_spacing: float,
    *,
    clearance: float | None = None,
    neck_trace_width: float | None = None,
    neck_pair_spacing: float | None = None,
    neck_clearance: float | None = None,
) -> "DifferentialRoutingStructure.Layer":
    """Build a fresh ``DifferentialRoutingStructure.Layer`` with the
    project-default loss / velocity / clearance values.

    Default clearances follow AMD UG863 H-multiplier rules for the
    high-perf 16-layer stripline stackup: main-routing clearance is the
    inter-byte data-strobe rule (``7 H``), neck-down clearance is the
    relaxed "Under SoC/DRAM" inter-byte rule (``2 H``). Override either
    if your channel uses a different group of nets on this layer.

    Neck-down trace geometry defaults to the same width / spacing as
    the main routing — pass ``neck_trace_width`` /
    ``neck_pair_spacing`` to use a different fanout impedance target
    (e.g., :py:data:`INNER_DIFF_100_TRACE_WIDTH` /
    :py:data:`INNER_DIFF_100_PAIR_SPACING` to encode UG863's 100 Ω
    fanout target).

    Each call returns a new instance — the caller chains
    ``.reference(...)`` and (optionally) ``.fence(...)`` on the result.
    """
    if clearance is None:
        clearance = _H_MUL_INTER_BYTE * _H_STRIPLINE
    if neck_clearance is None:
        neck_clearance = _H_MUL_NECK_INTER_BYTE * _H_STRIPLINE
    if neck_trace_width is None:
        neck_trace_width = trace_width
    if neck_pair_spacing is None:
        neck_pair_spacing = pair_spacing
    return DifferentialRoutingStructure.Layer(
        trace_width=trace_width,
        pair_spacing=pair_spacing,
        clearance=clearance,
        velocity=_VEL_STRIPLINE,
        insertion_loss=0.018,
        neck_down=DifferentialRoutingStructure.NeckDown(
            trace_width=neck_trace_width,
            pair_spacing=neck_pair_spacing,
            clearance=neck_clearance,
        ),
    )


def _diff_layers_3psh(
    trace_width: float,
    pair_spacing: float,
    *,
    fences: dict[int, type[Via]] | None = None,
    neck_trace_width: float | None = None,
    neck_pair_spacing: float | None = None,
    clearance: float | None = None,
    neck_clearance: float | None = None,
) -> dict[int, "DifferentialRoutingStructure.Layer"]:
    """Build a 6-layer differential routing dict — 3 shielded layers per
    side — covering the high-perf 16-layer stackup's full inner-stripline
    routing capacity.

    Layers populated:

    - Top half: index ``2`` (L3), ``4`` (L5), ``6`` (L7)
    - Bottom half: index ``-7`` (L10), ``-5`` (L12), ``-3`` (L14)

    Each layer references the GND plane immediately above and below it.
    Optional fence vias may be attached per layer through the ``fences``
    dict, keyed by signal-layer index.

    Args:
        trace_width: Diff-pair trace width (mm).
        pair_spacing: Centre-to-centre pair spacing (mm).
        fences: Optional dict from layer index to fence Via class.
            For consistent return-path control across the stack, supply
            all 6 (one per shielded layer) — leave any out to skip
            fencing on that layer.

    Returns:
        A layer dict ready to drop into
        :py:class:`DifferentialRoutingStructure`'s ``layers`` argument.
    """
    fences = fences or {}

    # Per-layer (above_ref, below_ref) GND plane indices.
    refs: dict[int, tuple[int, int]] = {
        2: (1, 3),    # L3 fenced by GPlane2 / GPlane4
        4: (3, 5),    # L5 fenced by GPlane4 / GPlane6
        6: (5, 7),    # L7 fenced by GPlane6 / GPlane8
        -7: (-8, -6), # L10 (mirror of L7) — GPlane9 / GPlane11
        -5: (-6, -4), # L12 (mirror of L5) — GPlane11 / GPlane13
        -3: (-4, -2), # L14 (mirror of L3) — GPlane13 / GPlane15
    }

    layers: dict[int, "DifferentialRoutingStructure.Layer"] = {}
    for idx, (above, below) in refs.items():
        layer = (
            _diff_layer(
                trace_width,
                pair_spacing,
                clearance=clearance,
                neck_trace_width=neck_trace_width,
                neck_pair_spacing=neck_pair_spacing,
                neck_clearance=neck_clearance,
            )
            .reference(above, 1.0)
            .reference(below, 1.0)
        )
        fence_via = fences.get(idx)
        if fence_via is not None:
            layer = layer.fence(fence_via, _FENCE, reference_layer=below)
        layers[idx] = layer
    return layers


def _se_layer(
    trace_width: float,
    *,
    clearance: float | None = None,
    neck_down_trace_width: float | None = None,
    neck_down_clearance: float | None = None,
) -> "RoutingStructure.Layer":
    """Build a fresh ``RoutingStructure.Layer`` (single-ended) with the
    project-default loss / velocity values.

    Default clearances follow AMD UG863 H-multiplier rules: main
    clearance defaults to the same-byte data rule (``2.5 H``);
    neck-down clearance defaults to the "Under SoC/DRAM" same-byte
    rule (``1 H``). Override per-call when a stricter inter-class
    rule applies on this layer.
    """
    if clearance is None:
        clearance = _H_MUL_DATA_SAME_BYTE * _H_STRIPLINE
    if neck_down_clearance is None:
        neck_down_clearance = _H_MUL_NECK_DATA_SAME_BYTE * _H_STRIPLINE
    return RoutingStructure.Layer(
        trace_width=trace_width,
        clearance=clearance,
        velocity=_VEL_STRIPLINE,
        insertion_loss=0.018,
        neck_down=RoutingStructure.NeckDown(
            trace_width=neck_down_trace_width
            if neck_down_trace_width is not None
            else trace_width,
            clearance=neck_down_clearance,
        ),
    )


# ---------------------------------------------------------------------------
# Substrate
# ---------------------------------------------------------------------------


class HighPerfSubstrate(Substrate):
    """8-layer HDI substrate with multi-impedance routing structures.

    The default :py:meth:`Substrate.routing_structure` and
    :py:meth:`Substrate.differential_routing_structure` lookup picks the
    closest match by impedance, so callers like
    :py:class:`LPDDR5Constraint` resolve their routing structures
    automatically without explicit binding.
    """

    @inline
    class stackup(HighPerfStackup):
        pass

    constraints = HighPerfFabRules()

    # --- Vias -----------------------------------------------------------------
    # BGA-escape laser uVias — one per shielded routing layer in the top
    # half. Provide depth options for fanout to L3, L5, or L7. Bottom-side
    # escape vias (mirror) can be added if needed.

    # Signal-carrying microvia PinModels. Each entry is the (delay,
    # loss) for the (start_layer, stop_layer) traversal, used by JITX
    # signal-integrity constraints. Values are first-order estimates
    # for laser-drilled stacked microvias on a 0.1 mm Dk-3.0 dielectric:
    # delay ≈ traversal_length / phase_velocity + parasitic ~3 ps,
    # loss ≈ 0.01 dB per dielectric layer at LPDDR5 frequencies. These
    # should be replaced with EM-simulated or measured values for any
    # serious design.
    class uVia_L1_L3(Via):
        """BGA-escape laser uVia from L1 (top) → L3 (shielded #1).
        Spans 1 GND plane (L2) and 2 dielectrics."""

        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 2
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True
        models = {(0, 2): PinModel(3e-12, 0.02)}

    class uVia_L1_L5(Via):
        """BGA-escape laser uVia from L1 (top) → L5 (shielded #2).
        Spans 2 GND planes (L2/L4) and 4 dielectrics."""

        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 4
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True
        models = {(0, 4): PinModel(5e-12, 0.04)}

    class uVia_L1_L7(Via):
        """BGA-escape laser uVia from L1 (top) → L7 (shielded #3).
        Spans 3 GND planes (L2/L4/L6) and 6 dielectrics."""

        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 6
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True
        models = {(0, 6): PinModel(7e-12, 0.06)}

    # Fence uVias — one per shielded signal layer, spanning the GND
    # planes immediately above and below it. Used by the diff-pair
    # routing structures via `.fence(...)`.

    class uFence_L2_L4(Via):
        """Fence uVia spanning GPlane2 ↔ GPlane4 — fences L3 (top stripline #1)."""

        type = ViaType.LaserDrill
        start_layer = 1
        stop_layer = 3
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L4_L6(Via):
        """Fence uVia spanning GPlane4 ↔ GPlane6 — fences L5 (top stripline #2)."""

        type = ViaType.LaserDrill
        start_layer = 3
        stop_layer = 5
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L6_L8(Via):
        """Fence uVia spanning GPlane6 ↔ GPlane8 — fences L7 (top stripline #3)."""

        type = ViaType.LaserDrill
        start_layer = 5
        stop_layer = 7
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L9_L11(Via):
        """Fence uVia spanning GPlane9 ↔ GPlane11 — fences L10 (mirror of L7)."""

        type = ViaType.LaserDrill
        start_layer = -8
        stop_layer = -6
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L11_L13(Via):
        """Fence uVia spanning GPlane11 ↔ GPlane13 — fences L12 (mirror of L5)."""

        type = ViaType.LaserDrill
        start_layer = -6
        stop_layer = -4
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L13_L15(Via):
        """Fence uVia spanning GPlane13 ↔ GPlane15 — fences L14 (mirror of L3)."""

        type = ViaType.LaserDrill
        start_layer = -4
        stop_layer = -2
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    # Half-stack stitching uVias — connect every GND plane in one half
    # so the engine can render via-stitched GND pours via the
    # `GndReturnTag().stitch_via(...)` rule defined in user circuits.

    class uStitch_L1_L8(Via):
        """Top-half GND stitch uVia (L1 ↔ L8) — full top-half plane stitching."""

        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 7
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True

    class uStitch_L9_L16(Via):
        """Bottom-half GND stitch uVia (L9 ↔ L16) — mirror of uStitch_L1_L8."""

        type = ViaType.LaserDrill
        start_layer = -8
        stop_layer = -1
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True

    class TH_Via(Via):
        """Mechanical through-hole — PTH components + top-to-bottom stitching."""

        type = ViaType.MechanicalDrill
        start_layer = Side.Top
        stop_layer = Side.Bottom
        diameter = 0.5
        hole_diameter = 0.25
        filled = True

    class TH_Via_Pwr(Via):
        """Mechanical through-hole, via-in-pad variant for power-rail
        stitching (GND + supply nets like VDD / VCC_SOC / VCC_AIE).

        Same body as :py:class:`TH_Via` but with ``via_in_pad`` enabled
        so the via sits inside a BGA ball pad — the shortest path from
        the pad to its reference plane on either side of the stack."""

        type = ViaType.MechanicalDrill
        start_layer = Side.Top
        stop_layer = Side.Bottom
        diameter = 0.5
        hole_diameter = 0.25
        filled = True
        via_in_pad = True

    # --- Routing structures --------------------------------------------------
    # All structures route on the inner stripline layers (3 per side =
    # 6 total). The shielded-layer geometry is built by the
    # `_diff_layers_3psh` and `_se_layer` helpers above, so each
    # structure here only declares its impedance / trace geometry.
    #
    # Fence vias (uFence_L2_L4, uFence_L4_L6, ..., uFence_L13_L15) are
    # **opt-in**, not used by any default routing structure. LPDDR5
    # routing per AMD UG863 doesn't require fencing alongside its
    # high-speed signals, and adding fence vias to the board's via list
    # by default would create unnecessary plate copper. Users who want
    # fenced diff-pair routing (e.g. for PCIe Gen 5+ or critical USB3
    # links) can either:
    #
    # 1. Subclass `HighPerfSubstrate` with custom diff routing structures
    #    that pass an explicit `fences=` dict to `_diff_layers_3psh`, and
    # 2. Subclass `HighPerfBoard` to add the corresponding `uFence_*`
    #    Via classes to its `vias` list.
    #
    # The map below is provided as a convenient starting point for that
    # opt-in path — pass it as `fences=_ALL_FENCES` if you want every
    # shielded layer fenced. It is not referenced by any default
    # routing structure.
    _ALL_FENCES: dict[int, type[Via]] = {
        2: uFence_L2_L4,    # L3
        4: uFence_L4_L6,    # L5
        6: uFence_L6_L8,    # L7
        -7: uFence_L9_L11,  # L10 (mirror of L7)
        -5: uFence_L11_L13, # L12 (mirror of L5)
        -3: uFence_L13_L15, # L14 (mirror of L3)
    }

    # 50 Ω single-ended stripline — DDR5 SE, legacy LPDDR5 DQ.
    # `symmetric_routing_layers` mirrors {2, 4, 6} → {-3, -5, -7} so the
    # same trace geometry applies on every shielded layer (3 per side).
    SE_50 = RoutingStructure(
        name="50 ohm Stripline",
        impedance=50 * ohm,
        layers=symmetric_routing_layers({
            i: _se_layer(
                INNER_SE_50_TRACE_WIDTH,
                neck_down_trace_width=INNER_SE_50_NECK_DOWN_WIDTH,
            )
            for i in (2, 4, 6)
        }),
    )

    # 40 Ω single-ended stripline — LPDDR5 DQ / DMI / CA / CS per AMD
    # UG863 (40 Ω ±10% single-ended), and LPDDR4 DQ.
    SE_40 = RoutingStructure(
        name="40 ohm Stripline",
        impedance=40 * ohm,
        layers=symmetric_routing_layers({
            i: _se_layer(
                INNER_SE_40_TRACE_WIDTH,
                clearance=_H_STRIPLINE * _H_MUL_DATA_SAME_BYTE,
                neck_down_trace_width=INNER_SE_40_NECK_DOWN_WIDTH,
                neck_down_clearance=INNER_SE_40_NECK_DOWN_CLEARANCE
            )
            for i in (2, 4, 6)
        }),
    )

    # 75 Ω differential stripline — LPDDR5 CK / WCK / RDQS per AMD UG863.
    # Main routing on the inner stripline layers at 75 Ω; neck-down
    # uses 100 Ω geometry (`INNER_DIFF_100_*`) which is UG863's spec
    # for the BGA fanout region under the SoC / DRAM. Layer clearance
    # = 5 H = 0.5 mm (CA-to-CK rule from UG863 §"Physical Design Rules"
    # — covers CK ↔ WCK / CK ↔ RDQS on the same layer); neck-down
    # clearance = 1 H = 0.1 mm (the relaxed "Under SoC/DRAM" within-
    # byte rule). No via fencing by default — opt in via fences=.
    DRS_DiffPair_75 = DifferentialRoutingStructure(
        name="75 ohm Differential Stripline",
        impedance=75 * ohm,
        layers=_diff_layers_3psh(
            INNER_DIFF_75_TRACE_WIDTH, INNER_DIFF_75_PAIR_SPACING,
            clearance=_H_MUL_CA_TO_CK * _H_STRIPLINE,
            neck_trace_width=INNER_DIFF_100_TRACE_WIDTH,
            neck_pair_spacing=INNER_DIFF_100_PAIR_SPACING,
            neck_clearance=_H_MUL_NECK_DATA_SAME_BYTE * _H_STRIPLINE,
        ),
        uncoupled_region=RoutingStructure(
            name="75 ohm Uncoupled (~38 ohm SE)",
            impedance=38 * ohm,
            layers=symmetric_routing_layers({
                i: _se_layer(INNER_DIFF_75_TRACE_WIDTH) for i in (2, 4, 6)
            }),
        ),
    )

    # 85 Ω differential stripline — PCIe, USB3. No fencing by default;
    # subclass and pass `fences=_ALL_FENCES` if your channel needs it.
    DRS_DiffPair_85 = DifferentialRoutingStructure(
        name="85 ohm Differential Stripline",
        impedance=85 * ohm,
        layers=_diff_layers_3psh(
            INNER_DIFF_85_TRACE_WIDTH, INNER_DIFF_85_PAIR_SPACING,
        ),
        uncoupled_region=RoutingStructure(
            name="85 ohm Uncoupled (~42 ohm SE)",
            impedance=42 * ohm,
            layers=symmetric_routing_layers({
                i: _se_layer(INNER_DIFF_85_TRACE_WIDTH) for i in (2, 4, 6)
            }),
        ),
    )

    # 100 Ω differential stripline — legacy LPDDR5 (the new default is
    # `DRS_DiffPair_75` per AMD UG863); kept for backward compatibility
    # with non-AMD-spec designs. No fencing by default — see _ALL_FENCES.
    DRS_DiffPair_100 = DifferentialRoutingStructure(
        name="100 ohm Differential Stripline",
        impedance=100 * ohm,
        layers=_diff_layers_3psh(
            INNER_DIFF_100_TRACE_WIDTH, INNER_DIFF_100_PAIR_SPACING,
        ),
        uncoupled_region=RoutingStructure(
            name="100 ohm Uncoupled (~50 ohm SE)",
            impedance=50 * ohm,
            layers=symmetric_routing_layers({
                i: _se_layer(INNER_DIFF_100_TRACE_WIDTH) for i in (2, 4, 6)
            }),
        ),
    )

    # 90 Ω differential stripline — USB2. No fencing.
    DRS_DiffPair_90 = DifferentialRoutingStructure(
        name="90 ohm Differential Stripline",
        impedance=90 * ohm,
        layers=_diff_layers_3psh(
            INNER_DIFF_90_TRACE_WIDTH, INNER_DIFF_90_PAIR_SPACING,
        ),
        uncoupled_region=RoutingStructure(
            name="90 ohm Uncoupled (~45 ohm SE)",
            impedance=45 * ohm,
            layers=symmetric_routing_layers({
                i: _se_layer(INNER_DIFF_90_TRACE_WIDTH) for i in (2, 4, 6)
            }),
        ),
    )

    # No tag-based clearance rules. The chaos_hfss original had a
    # DiffPair-to-GND-pour clearance rule keyed off DiffPairTag /
    # GndReturnTag, but those tags were never applied to any net in this
    # project so the rule was dead. Add similar rules in user circuits
    # if needed, using the signal-type tags from
    # `jitx_protocols_ext.protocols.memory.lpddr_constraints`.


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

# Board outline — sized to comfortably fit a 37.5 mm BGA + DRAM + decoupling.
_HIGH_PERF_BOARD_SHAPE = rectangle(80.0, 80.0, radius=4)
_HIGH_PERF_SIGNAL_AREA = ShapelyGeometry.from_shape(_HIGH_PERF_BOARD_SHAPE).buffer(-0.5)


class HighPerfBoard(Board):
    """80 mm × 80 mm board on the HDI substrate."""

    shape = _HIGH_PERF_BOARD_SHAPE
    signal_area = _HIGH_PERF_BOARD_SHAPE
    substrate = HighPerfSubstrate
    vias = [
        # BGA-escape vias to each shielded routing layer
        HighPerfSubstrate.uVia_L1_L3,
        HighPerfSubstrate.uVia_L1_L5,
        HighPerfSubstrate.uVia_L1_L7,
        # Half-stack GND stitching uVias
        HighPerfSubstrate.uStitch_L1_L8,
        HighPerfSubstrate.uStitch_L9_L16,
        # Mechanical through-hole
        HighPerfSubstrate.TH_Via,
        HighPerfSubstrate.TH_Via_Pwr,
        # Fence uVias (uFence_L2_L4, uFence_L4_L6, uFence_L6_L8,
        # uFence_L9_L11, uFence_L11_L13, uFence_L13_L15) are
        # intentionally NOT registered here. LPDDR5 per AMD UG863 does
        # not require fence vias, and registering unused via types
        # bloats the board's via inventory. Subclass `HighPerfBoard` and
        # extend this list if your routing structures opt into
        # `.fence(...)` (see `_ALL_FENCES` on the substrate).
    ]
