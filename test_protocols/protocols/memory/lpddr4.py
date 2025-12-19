"""LPDDR4 Memory Protocol

LPDDR4 is a point-to-point high speed memory protocol.
https://en.wikipedia.org/wiki/LPDDR

This file contains functions and definitions for supporting LPDDR4
connections between microprocessors and memories in a board design.

## LPDDR4 Constraints

Values based on AMD Ultrascale PCB Design Guide Chapter 2:
https://docs.amd.com/v/u/en-US/ug583-ultrascale-pcb-design

- CK Intra-pair Skew: ±2.0ps
- CK to CKE Skew: ±8.0ps
- CK to CS Skew: ±8.0ps
- CK to CA Skew: ±8.0ps
- CK to DQS Skew: -500ps to +2500ps
- DQS Intra-pair Skew: ±2.0ps
- DQS to DQ/DMI Skew: ±5.0ps
- DQ/DMI to DQ/DMI Skew: ±5.0ps
- Maximum Signal Loss: 5.0dB
"""

from __future__ import annotations
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from jitx import current
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


class LPDDR4Width(Enum):
    """LPDDR4 Channel Width

    LPDDR4 supports x16, x32, and x64 configurations.
    """

    x16 = 16
    "16-bit width (1 x16 channel)"
    x32 = 32
    "32-bit width (2 x16 channels)"
    x64 = 64
    "64-bit width (4 x16 channels)"


def width_to_int(width: LPDDR4Width) -> int:
    """Convert LPDDR4 width enum to integer bit width

    Args:
        width: LPDDR4 width enum

    Returns:
        Number of bits
    """
    return width.value


def num_x16_lanes(width: LPDDR4Width) -> int:
    """Get number of x16 channels for given width

    Args:
        width: LPDDR4 width enum

    Returns:
        Number of x16 channels
    """
    if width == LPDDR4Width.x16:
        return 1
    elif width == LPDDR4Width.x32:
        return 2
    elif width == LPDDR4Width.x64:
        return 4
    else:
        raise ValueError(f"Unknown LPDDR4 width: {width}")


class LPDDR4Rank(Enum):
    """LPDDR4 Rank Configuration"""

    Rank1 = 1
    "Single rank"
    Rank2 = 2
    "Dual rank"
    Rank3 = 3
    "Triple rank"


class LPDDR4Lane(Port):
    """LPDDR4 Byte Lane Bundle

    One byte lane with 8 DQ, 1 DQS pair, and 1 DMI signal.

    Attributes:
        dq: 8-bit data bus
        dqs: Data strobe differential pair
        dmi: Data mask/inversion signal
    """

    dq = [Port() for _ in range(8)]
    "8-bit data bus"

    dqs = DiffPair()
    "Data strobe differential pair"

    dmi = Port()
    "Data mask/inversion signal"


class LPDDR4_X16(Port):
    """LPDDR4 x16 Channel Bundle

    One x16 channel with 2 byte lanes, clock, and control signals.

    Args:
        rank: Rank configuration

    Attributes:
        d: 2 byte lanes (16 bits total)
        ck: Clock differential pair
        cke: Clock enable signals (1 per rank)
        cs: Chip select signals (1 per rank)
        ca: Command/address bus (6 bits)
    """

    d: Sequence[LPDDR4Lane]
    "2 byte lanes"

    ck = DiffPair()
    "Clock differential pair"

    cke: Sequence[Port]
    "Clock enable signals"

    cs: Sequence[Port]
    "Chip select signals"

    ca = [Port() for _ in range(6)]
    "Command/address bus (6 bits)"

    def __init__(self, rank: LPDDR4Rank):
        rank_count = rank.value
        self.d = tuple(LPDDR4Lane() for _ in range(2))
        self.cke = tuple(Port() for _ in range(rank_count))
        self.cs = tuple(Port() for _ in range(rank_count))


class LPDDR4(Port):
    """LPDDR4 Memory Bundle

    Complete LPDDR4 interface with multiple x16 channels.

    Args:
        width: Total channel width (x16, x32, or x64)
        rank: Rank configuration

    Attributes:
        ch: Array of x16 channels
    """

    ch: Sequence[LPDDR4_X16]
    "Array of x16 channels"

    def __init__(self, width: LPDDR4Width, rank: LPDDR4Rank):
        channel_count = num_x16_lanes(width)
        self.ch = tuple(LPDDR4_X16(rank) for _ in range(channel_count))


@dataclass(frozen=True)
class LPDDR4ConstraintParams:
    """LPDDR4 Constraint Parameters

    All timing and loss constraints for LPDDR4.

    Attributes:
        skew_ck: CK intra-pair skew (±2.0ps)
        skew_ck_cke: CK to CKE skew (±8.0ps)
        skew_ck_cs: CK to CS skew (±8.0ps)
        skew_ck_ca: CK to CA skew (±8.0ps)
        skew_ck_dqs: CK to DQS skew (-500ps to +2500ps)
        skew_dqs: DQS intra-pair skew (±2.0ps)
        skew_dqs_dq: DQS to DQ/DMI skew (±5.0ps)
        skew_dq_dq: DQ/DMI to DQ/DMI skew (±5.0ps)
        loss: Maximum signal loss (5.0dB)
    """

    skew_ck: Toleranced = Toleranced(0, 2.0e-12)
    skew_ck_cke: Toleranced = Toleranced(0, 8.0e-12)
    skew_ck_cs: Toleranced = Toleranced(0, 8.0e-12)
    skew_ck_ca: Toleranced = Toleranced(0, 8.0e-12)
    skew_ck_dqs: Toleranced = Toleranced.min_max(-500.0e-12, 2500.0e-12)
    skew_dqs: Toleranced = Toleranced(0, 2.0e-12)
    skew_dqs_dq: Toleranced = Toleranced(0, 5.0e-12)
    skew_dq_dq: Toleranced = Toleranced(0, 5.0e-12)
    loss: float = 5.0


@inner
class LPDDR4Constraint(SignalConstraint["LPDDR4"]):
    """Signal Integrity Constraint for LPDDR4

    Applies comprehensive timing and routing constraints to all LPDDR4 signals.

    Args:
        width: Channel width
        rank: Rank configuration
        params: Constraint parameters
        diff_structure: Differential routing structure for CK and DQS
        se_structure: Single-ended routing structure for other signals
    """

    def __init__(
        self,
        width: LPDDR4Width,
        rank: LPDDR4Rank,
        params: LPDDR4ConstraintParams | None = None,
        diff_structure: DifferentialRoutingStructure | None = None,
        se_structure: RoutingStructure | None = None,
    ):
        super().__init__()
        self.width = width
        self.rank = rank
        self.params = params or LPDDR4ConstraintParams()

        if not diff_structure:
            # LPDDR4 uses 80Ω differential impedance for CK/DQS
            diff_structure = current.substrate.differential_routing_structure(
                Toleranced.percent(85, 5)
            )
        if not se_structure:
            # LPDDR4 uses ~40Ω single-ended impedance
            se_structure = current.substrate.routing_structure(Toleranced.percent(40, 10))

        self.ck_constraint = DiffPairConstraint(
            skew=self.params.skew_ck, loss=self.params.loss, structure=diff_structure
        )
        self.dqs_constraint = DiffPairConstraint(
            skew=self.params.skew_dqs, loss=self.params.loss, structure=diff_structure
        )
        self.se_structure = se_structure

    def constrain(self, src: LPDDR4, dst: LPDDR4):
        """Apply all LPDDR4 constraints

        Args:
            src: Source LPDDR4 port
            dst: Destination LPDDR4 port
        """
        n16 = num_x16_lanes(self.width)
        nr = self.rank.value

        # Constrain each x16 channel
        for src_ch, dst_ch in zip(src.ch[:n16], dst.ch[:n16], strict=True):
            # CK intra-pair constraint
            self.ck_constraint.constrain(src_ch.ck, dst_ch.ck)

            # Use CK.P as timing reference for this channel
            guide_ck = Topology(src_ch.ck.p, dst_ch.ck.p)

            # CK to CKE/CS timing
            for i in range(nr):
                # CKE
                cke_topo = Topology(src_ch.cke[i], dst_ch.cke[i])
                self.add(
                    ConstrainReferenceDifference(guide_ck, [cke_topo]).timing_difference(
                        self.params.skew_ck_cke
                    )
                )
                cke_constrained = Constrain(cke_topo).insertion_loss(self.params.loss)
                cke_constrained.structure(self.se_structure)
                self.add(cke_constrained)

                # CS
                cs_topo = Topology(src_ch.cs[i], dst_ch.cs[i])
                self.add(
                    ConstrainReferenceDifference(guide_ck, [cs_topo]).timing_difference(
                        self.params.skew_ck_cs
                    )
                )
                cs_constrained = Constrain(cs_topo).insertion_loss(self.params.loss)
                cs_constrained.structure(self.se_structure)
                self.add(cs_constrained)

            # CK to CA timing
            for src_ca, dst_ca in zip(src_ch.ca, dst_ch.ca, strict=True):
                ca_topo = Topology(src_ca, dst_ca)
                self.add(
                    ConstrainReferenceDifference(guide_ck, [ca_topo]).timing_difference(
                        self.params.skew_ck_ca
                    )
                )
                ca_constrained = Constrain(ca_topo).insertion_loss(self.params.loss)
                ca_constrained.structure(self.se_structure)
                self.add(ca_constrained)

            # Constrain each byte lane (2 lanes per x16 channel)
            for src_lane, dst_lane in zip(src_ch.d, dst_ch.d, strict=True):
                # DQS intra-pair
                self.dqs_constraint.constrain(src_lane.dqs, dst_lane.dqs)

                # DQS timing reference
                guide_dqs = Topology(src_lane.dqs.p, dst_lane.dqs.p)

                # CK to DQS timing
                self.add(
                    ConstrainReferenceDifference(guide_ck, [guide_dqs]).timing_difference(
                        self.params.skew_ck_dqs
                    )
                )

                # DQS to DQ timing
                for src_dq, dst_dq in zip(src_lane.dq, dst_lane.dq, strict=True):
                    dq_topo = Topology(src_dq, dst_dq)
                    self.add(
                        ConstrainReferenceDifference(guide_dqs, [dq_topo]).timing_difference(
                            self.params.skew_dqs_dq
                        )
                    )
                    dq_constrained = Constrain(dq_topo).insertion_loss(self.params.loss)
                    dq_constrained.structure(self.se_structure)
                    self.add(dq_constrained)

                # DQS to DMI timing
                dmi_topo = Topology(src_lane.dmi, dst_lane.dmi)
                self.add(
                    ConstrainReferenceDifference(guide_dqs, [dmi_topo]).timing_difference(
                        self.params.skew_dqs_dq
                    )
                )
                dmi_constrained = Constrain(dmi_topo).insertion_loss(self.params.loss)
                dmi_constrained.structure(self.se_structure)
                self.add(dmi_constrained)

                # DQ/DMI to DQ/DMI pair-wise skew (use DMI as reference)
                for i in range(1, 8):
                    dq_topo = Topology(src_lane.dq[i], dst_lane.dq[i])
                    self.add(
                        ConstrainReferenceDifference(dmi_topo, [dq_topo]).timing_difference(
                            self.params.skew_dq_dq * 0.5
                        )
                    )
