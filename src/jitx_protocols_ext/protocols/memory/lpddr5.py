"""LPDDR5/LPDDR5X Memory Protocol.

LPDDR5/LPDDR5X is a high-speed memory protocol for mobile and low-power
applications. https://en.wikipedia.org/wiki/LPDDR

This file supports single channel, dual channel, and quad channel
configurations with rank = 1 or 2. The implementation supports both
LPDDR5 and LPDDR5X protocols.

## Key Features

- Dual-channel (x32) and quad-channel (x64) configurations
- Single and dual rank support
- Write Clock (WCK) and Read Data Strobe (RDQS) for improved timing margins
- Command/Address (CA) bus with 7-bit width per channel
- Strict timing requirements for high-speed operation

## LPDDR5 Routing Constraints (per AMD UG863, Versal PCB Design Guide)

Source: https://docs.amd.com/r/en-US/ug863-versal-pcb-design/Timing-Constraint-Rules-for-LPDDR5/5x-Signals

| Constraint                | UG863 value     | Notes                              |
|---------------------------|-----------------|------------------------------------|
| CK / WCK / RDQS intra-pair| 0 to +2 ps      | T leads C, asymmetric              |
| CK to CS                  | ±20 ps          | symmetric                          |
| CK to CA                  | ±50 ps          | symmetric                          |
| CK to WCK                 | ±50 ps          | symmetric (PCB *flight-time* match;|
|                           |                 |  not the JEDEC tWCK-CK protocol    |
|                           |                 |  offset which is a controller-     |
|                           |                 |  programmed phase, ~250..1250 ps)  |
| Data (DQ/DMI) to WCK      | ±50 ps          | symmetric, write direction         |
| Data (DQ/DMI) to RDQS     | 0 to +80 ps     | data must lead RDQS, asymmetric    |

UG863 also specifies (not modelled by `LPDDR5ConstraintParams`):
- Single-ended impedance: 40 Ω ±10% (up to 55 Ω in BGA fanout area)
- Differential impedance: 75 Ω ±10% (up to 100 Ω in BGA fanout area)
- Maximum trace length: 2000 mil (~50.8 mm) for both CAC/CK and data
- Maximum 2 vias per data, WCK, or RDQS net
- 2:1 signal-to-GND via ratio on the SoC side
- Trace spacing: 2.5 H trace-to-trace (1 H under SoC/DRAM)

UG863 does not give an insertion-loss limit. We default to 4.0 dB —
industry-typical for ~6.4 Gbps LPDDR5; override via `LPDDR5ConstraintParams`
if your channel needs differ.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from jitx.container import inner
from jitx.net import DiffPair, Port
from jitx.si import (
    Constrain,
    ConstrainReferenceDifference,
    DiffPairConstraint,
    DifferentialRoutingStructure,
    RoutingStructure,
    SignalConstraint,
    Topology,
)
from jitx.toleranced import Toleranced


class LPDDR5Width(Enum):
    """LPDDR5 Channel Width"""

    x32 = 32
    "32-bit width (dual x16 channel)"
    x64 = 64
    "64-bit width (quad x16 channel)"


def width_to_int(width: LPDDR5Width) -> int:
    return width.value


def num_channels(width: LPDDR5Width) -> int:
    """Get number of x16 channels

    Args:
        width: LPDDR5 width

    Returns:
        Number of x16 channels
    """
    if width == LPDDR5Width.x32:
        return 2
    if width == LPDDR5Width.x64:
        return 4
    raise ValueError(f"Unknown LPDDR5 width: {width}")


class LPDDR5Rank(Enum):
    """LPDDR5 Rank Configuration"""

    SingleRank = 1
    DualRank = 2


def rank_to_int(rank: LPDDR5Rank) -> int:
    """Convert LPDDR5 rank enum to integer count of CS signals per channel.

    Args:
        rank: LPDDR5 rank enum

    Returns:
        Number of CS signals per channel
    """
    return rank.value


class LPDDR5DataLane(Port):
    """LPDDR5 x8 Data Lane Bundle

    Attributes:
        dq: 8-bit data bus
        dmi: Data mask/inversion
        wck: Write clock differential pair
        rdqs: Read data strobe differential pair
    """

    dq = [Port() for _ in range(8)]
    wck = DiffPair()
    dmi = Port()
    rdqs = DiffPair()


class LPDDR5(Port):
    """LPDDR5 Memory Bundle

    Complete LPDDR5 interface.

    Args:
        width: Channel width (x32 or x64)
        rank: Rank configuration

    Attributes:
        d: 2D array [channels][lanes] of data lanes
        cs: 2D array [channels][ranks] of chip selects
        ck: Clock pairs (1 per channel)
        ca: 2D array [channels][7] of command/address
        reset_n: Shared reset signal
    """

    d: Sequence[Sequence[LPDDR5DataLane]]
    cs: Sequence[Sequence[Port]]
    ck: Sequence[DiffPair]
    ca: Sequence[Sequence[Port]]
    reset_n = Port()

    def __init__(self, width: LPDDR5Width, rank: LPDDR5Rank):
        num_ch = num_channels(width)
        rank_count = rank.value

        # Each channel has 2 data lanes
        self.d = tuple(tuple(LPDDR5DataLane() for _ in range(2)) for _ in range(num_ch))
        # CS per channel per rank
        self.cs = tuple(tuple(Port() for _ in range(rank_count)) for _ in range(num_ch))
        # CK per channel
        self.ck = tuple(DiffPair() for _ in range(num_ch))
        # CA per channel (7 bits)
        self.ca = tuple(tuple(Port() for _ in range(7)) for _ in range(num_ch))


@dataclass(frozen=True)
class LPDDR5Impedances:
    """LPDDR5 Impedance Specifications (AMD UG863).

    Defaults follow AMD UG863 §"Physical Design Rules for LPDDR5/5x Signals":
    differential 75 Ω ±10% and single-ended 40 Ω ±10%. UG863 also notes the
    impedance can climb to 100 Ω diff / 55 Ω SE in the BGA fanout area
    under the SoC or DRAM — that local exception is *not* modelled by these
    fields; if your fanout geometry forces it, configure a separate routing
    structure on the substrate and bind it via the ``*_structure`` arguments
    on :py:class:`LPDDR5Constraint`.

    Attributes:
        ck_impedance: CK differential impedance (default: 75 Ω ±10%)
        wck_rdqs_impedance: WCK/RDQS differential impedance (default: 75 Ω ±10%)
        dq_impedance: DQ/DMI single-ended impedance (default: 40 Ω ±10%)
        ca_impedance: CA/CS single-ended impedance (default: 40 Ω ±10%)
    """

    ck_impedance: Toleranced = Toleranced.percent(75, 10)
    "CK differential impedance"

    wck_rdqs_impedance: Toleranced = Toleranced.percent(75, 10)
    "WCK/RDQS differential impedance"

    dq_impedance: Toleranced = Toleranced.percent(40, 10)
    "DQ/DMI single-ended impedance"

    ca_impedance: Toleranced = Toleranced.percent(40, 10)
    "CA/CS single-ended impedance"


@dataclass(frozen=True)
class LPDDR5ConstraintParams:
    """LPDDR5 Constraint Parameters (AMD UG863).

    Default skew values follow AMD UG863 Table "Timing Constraint Rules
    for LPDDR5/5x Signals". The intra-pair and Data-to-RDQS ranges are
    asymmetric (positive-only) per the source; they're encoded with
    :py:meth:`Toleranced.min_max` to preserve that asymmetry. The other
    skews are symmetric, encoded as ``Toleranced(0, X)``.

    Note on CK-to-WCK: UG863 specifies a ±50 ps PCB *flight-time* match.
    Earlier versions of this code used –250 to +1250 ps, mistaking the
    JEDEC tWCK-CK protocol-level offset (a controller-programmed phase,
    not a routing tolerance) for a routing constraint.

    Note on CK-to-RDQS: UG863 does not specify CK-to-RDQS skew; only
    Data-to-RDQS. RDQS is memory-driven, so matching its trace flight
    time to controller-driven CK isn't meaningful. The previous
    ``skew_ck_rdqs`` field has been removed accordingly.

    The ``loss`` value (4.0 dB) is not from UG863 — AMD doesn't publish
    a loss limit. 4 dB is industry-typical for ~6.4 Gbps LPDDR5; tune
    for your channel.
    """

    skew_ck: Toleranced = Toleranced.min_max(0, 2.0e-12)
    "CK intra-pair skew (T leads C). UG863: 0 to +2 ps."

    skew_ck_cs: Toleranced = Toleranced(0, 20.0e-12)
    "CK to CS skew. UG863: ±20 ps."

    skew_ck_ca: Toleranced = Toleranced(0, 50.0e-12)
    "CK to CA skew. UG863: ±50 ps."

    skew_ck_wck: Toleranced = Toleranced(0, 50.0e-12)
    "CK to WCK trace-flight-time match. UG863: ±50 ps."

    skew_wck: Toleranced = Toleranced.min_max(0, 2.0e-12)
    "WCK intra-pair skew (T leads C). UG863: 0 to +2 ps."

    skew_rdqs: Toleranced = Toleranced.min_max(0, 2.0e-12)
    "RDQS intra-pair skew (T leads C). UG863: 0 to +2 ps."

    skew_wck_dq: Toleranced = Toleranced(0, 50.0e-12)
    "DQ/DMI to WCK skew (write direction). UG863: ±50 ps."

    skew_rdqs_dq: Toleranced = Toleranced.min_max(0, 80.0e-12)
    "DQ/DMI to RDQS skew (read direction, data leads RDQS). UG863: 0 to +80 ps."

    loss: float = 4.0
    "Maximum insertion loss (dB). Not in UG863; default is industry practice."


@inner
class LPDDR5Constraint(SignalConstraint["LPDDR5"]):
    """Signal Integrity Constraint for LPDDR5.

    Applies skew (intra-pair, CK-to-CS, CK-to-CA, CK-to-WCK, DQ-to-WCK,
    DQ-to-RDQS) and per-topology insertion-loss budgets to an LPDDR5
    src/dst pair, and optionally binds per-signal-class
    :py:class:`RoutingStructure` / :py:class:`DifferentialRoutingStructure`
    on each topology.

    The ``*_structure`` parameters are independent — bind any subset.
    For tag-based rule application (paired with
    :py:func:`lpddr_constraints.make_lpddr_routing_rules` and
    :py:func:`lpddr_constraints.make_lpddr_spacing_rules`), leave them
    all at ``None``; the tag rules then drive trace geometry. The two
    layers compose: routing-structure clearance is the per-layer
    minimum, tag rules enforce stricter cross-class clearances on top.

    Args:
        width: Channel width
        rank: Rank configuration
        params: Constraint parameters (skew + loss). Use defaults
            derived from AMD UG863 unless your channel needs
            different values.
        dq_structure: Single-ended :py:class:`RoutingStructure` for
            DQ + DMI (per byte lane). Defaults to ``None``.
        ca_structure: Single-ended :py:class:`RoutingStructure` for
            CA + CSn + RESET_N. Defaults to ``None``.
        ck_structure: :py:class:`DifferentialRoutingStructure` for
            CK pairs. Defaults to ``None``.
        wck_structure: :py:class:`DifferentialRoutingStructure` for
            WCK pairs. Defaults to ``None``.
        rdqs_structure: :py:class:`DifferentialRoutingStructure` for
            RDQS pairs. Defaults to ``None``.
    """

    def __init__(
        self,
        width: LPDDR5Width,
        rank: LPDDR5Rank,
        params: LPDDR5ConstraintParams | None = None,
        *,
        dq_structure: RoutingStructure | None = None,
        ca_structure: RoutingStructure | None = None,
        ck_structure: DifferentialRoutingStructure | None = None,
        wck_structure: DifferentialRoutingStructure | None = None,
        rdqs_structure: DifferentialRoutingStructure | None = None,
    ):
        super().__init__()
        self.width = width
        self.rank = rank
        self.params = params or LPDDR5ConstraintParams()
        self.dq_structure = dq_structure
        self.ca_structure = ca_structure

        # Diff-pair constraints embed their routing structure directly
        # so DiffPairConstraint.constrain() applies it on each
        # ConstrainDiffPair.
        self.ck_constraint = DiffPairConstraint(
            skew=self.params.skew_ck, loss=self.params.loss,
            structure=ck_structure,
        )
        self.wck_constraint = DiffPairConstraint(
            skew=self.params.skew_wck, loss=self.params.loss,
            structure=wck_structure,
        )
        self.rdqs_constraint = DiffPairConstraint(
            skew=self.params.skew_rdqs, loss=self.params.loss,
            structure=rdqs_structure,
        )

    def constrain(self, src: LPDDR5, dst: LPDDR5):
        """Apply all LPDDR5 constraints

        Args:
            src: Source LPDDR5 port
            dst: Destination LPDDR5 port

        Note:
            This method does **not** apply signal-type tags to the link.
            Tag application is the caller's responsibility (the example
            should call :py:func:`lpddr_constraints.tag_lpddr_link` on
            the require()-resolved ports *outside* the
            ``constrain_topology`` context — JITX rejects property
            mutation on the placeholder ports passed to ``constrain``).
        """
        num_ch = num_channels(self.width)
        nr = self.rank.value

        # Constrain each channel
        for ch_idx in range(num_ch):
            src_ch_ck = src.ck[ch_idx]
            dst_ch_ck = dst.ck[ch_idx]

            # CK constraint
            self.ck_constraint.constrain(src_ch_ck, dst_ch_ck)
            guide_ck = Topology(src_ch_ck.p, dst_ch_ck.p)

            # CS and CA timing relative to CK + per-net insertion loss.
            # If `ca_structure` is supplied, bind it on every CS / CA
            # topology — otherwise tag-based rules drive geometry.
            for rank_idx in range(nr):
                cs_topo = Topology(src.cs[ch_idx][rank_idx], dst.cs[ch_idx][rank_idx])
                self.add(
                    ConstrainReferenceDifference(guide_ck, [cs_topo]).timing_difference(
                        self.params.skew_ck_cs
                    )
                )
                cs_constraint = Constrain(cs_topo).insertion_loss(self.params.loss)
                if self.ca_structure is not None:
                    cs_constraint.structure(self.ca_structure)
                self.add(cs_constraint)

            for ca_bit in range(7):
                ca_topo = Topology(src.ca[ch_idx][ca_bit], dst.ca[ch_idx][ca_bit])
                self.add(
                    ConstrainReferenceDifference(guide_ck, [ca_topo]).timing_difference(
                        self.params.skew_ck_ca
                    )
                )
                ca_constraint = Constrain(ca_topo).insertion_loss(self.params.loss)
                if self.ca_structure is not None:
                    ca_constraint.structure(self.ca_structure)
                self.add(ca_constraint)

            # Constrain data lanes (2 per channel)
            for lane_idx in range(2):
                src_lane = src.d[ch_idx][lane_idx]
                dst_lane = dst.d[ch_idx][lane_idx]

                # WCK and RDQS constraints
                self.wck_constraint.constrain(src_lane.wck, dst_lane.wck)
                self.rdqs_constraint.constrain(src_lane.rdqs, dst_lane.rdqs)

                guide_wck = Topology(src_lane.wck.p, dst_lane.wck.p)
                guide_rdqs = Topology(src_lane.rdqs.p, dst_lane.rdqs.p)

                # CK to WCK trace-flight-time match (UG863: ±50 ps).
                # No CK-to-RDQS constraint — UG863 doesn't specify one,
                # since RDQS is memory-driven and matching its trace
                # length to controller-driven CK isn't meaningful.
                self.add(
                    ConstrainReferenceDifference(guide_ck, [guide_wck]).timing_difference(
                        self.params.skew_ck_wck
                    )
                )

                # DQ and DMI constraints — timing relative to WCK + RDQS,
                # plus per-topology insertion-loss limit. If
                # `dq_structure` is supplied, bind it on each DQ / DMI
                # topology — otherwise tag-based rules drive geometry.
                for src_dq, dst_dq in zip(src_lane.dq, dst_lane.dq, strict=True):
                    dq_topo = Topology(src_dq, dst_dq)
                    self.add(
                        ConstrainReferenceDifference(guide_wck, [dq_topo]).timing_difference(
                            self.params.skew_wck_dq
                        )
                    )
                    self.add(
                        ConstrainReferenceDifference(guide_rdqs, [dq_topo]).timing_difference(
                            self.params.skew_rdqs_dq
                        )
                    )
                    dq_constraint = Constrain(dq_topo).insertion_loss(self.params.loss)
                    if self.dq_structure is not None:
                        dq_constraint.structure(self.dq_structure)
                    self.add(dq_constraint)

                # DMI constraints
                dmi_topo = Topology(src_lane.dmi, dst_lane.dmi)
                self.add(
                    ConstrainReferenceDifference(guide_wck, [dmi_topo]).timing_difference(
                        self.params.skew_wck_dq
                    )
                )
                dmi_constraint = Constrain(dmi_topo).insertion_loss(self.params.loss)
                if self.dq_structure is not None:
                    dmi_constraint.structure(self.dq_structure)
                self.add(dmi_constraint)

        # Reset signal (shared across all channels) — loss only.
        # `ca_structure` covers RESET_N too — same geometry class as
        # CA / CSn (controller-driven single-ended) per UG863.
        reset_topo = Topology(src.reset_n, dst.reset_n)
        reset_constraint = Constrain(reset_topo).insertion_loss(self.params.loss)
        if self.ca_structure is not None:
            reset_constraint.structure(self.ca_structure)
        self.add(reset_constraint)


def connect_lpddr5(
    src: LPDDR5,
    dst: LPDDR5,
    width: LPDDR5Width,
    rank: LPDDR5Rank = LPDDR5Rank.SingleRank,
):
    """Connect and constrain an LPDDR5 discrete point-to-point link.

    Convenience function that creates an :py:class:`LPDDR5Constraint`
    and applies it via ``constrain_topology``. The constraint binds
    skew + insertion-loss limits — no routing structures. Trace width
    / spacing / pair spacing are expected to come from the tag-based
    design rules in :py:mod:`lpddr_constraints`
    (:py:func:`make_lpddr_routing_rules`,
    :py:func:`make_lpddr_spacing_rules`).

    Args:
        src: Source LPDDR5 port (controller side)
        dst: Destination LPDDR5 port (memory side)
        width: Channel width (x32 or x64)
        rank: Rank configuration (default: SingleRank)

    Returns:
        The LPDDR5Constraint that was applied.
    """
    constraint = LPDDR5Constraint(width=width, rank=rank)
    constraint.constrain_topology(src, dst)
    return constraint
