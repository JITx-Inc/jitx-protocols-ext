"""LPDDR5/LPDDR5X Memory Protocol

LPDDR5/LPDDR5X is a high-speed memory protocol for mobile and low-power applications.
https://en.wikipedia.org/wiki/LPDDR

This file supports single channel, dual channel, and quad channel configurations
with rank = 1 or 2. The implementation supports both LPDDR5 and LPDDR5X protocols.

## Key Features

- Dual-channel (x32) and quad-channel (x64) configurations
- Single and dual rank support
- Write Clock (WCK) and Read Data Strobe (RDQS) for improved timing margins
- Command/Address (CA) bus with 7-bit width per channel
- Strict timing requirements for high-speed operation

## LPDDR5 Constraints

- CK Intra-pair Skew: ±1.0ps
- CK to CS Skew: ±4.0ps
- CK to CA Skew: ±4.0ps
- CK to WCK/RDQS Skew: -250ps to +1250ps
- WCK/RDQS Intra-pair Skew: ±1.0ps
- WCK/RDQS to DQ/DMI Skew: ±2.5ps
- DQ/DMI to DQ/DMI Skew: ±2.5ps
- Maximum Signal Loss: 4.0dB
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
    elif width == LPDDR5Width.x64:
        return 4
    else:
        raise ValueError(f"Unknown LPDDR5 width: {width}")


class LPDDR5Rank(Enum):
    """LPDDR5 Rank Configuration"""

    SingleRank = 1
    DualRank = 2


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
class LPDDR5ConstraintParams:
    """LPDDR5 Constraint Parameters"""

    skew_ck: Toleranced = Toleranced(0, 1.0e-12)
    skew_ck_cs: Toleranced = Toleranced(0, 4.0e-12)
    skew_ck_ca: Toleranced = Toleranced(0, 4.0e-12)
    skew_ck_wck: Toleranced = Toleranced.min_max(-250.0e-12, 1250.0e-12)
    skew_ck_rdqs: Toleranced = Toleranced.min_max(-250.0e-12, 1250.0e-12)
    skew_wck: Toleranced = Toleranced(0, 1.0e-12)
    skew_rdqs: Toleranced = Toleranced(0, 1.0e-12)
    skew_wck_dq: Toleranced = Toleranced(0, 2.5e-12)
    skew_rdqs_dq: Toleranced = Toleranced(0, 2.5e-12)
    skew_dq_dq: Toleranced = Toleranced(0, 2.5e-12)
    loss: float = 4.0


@inner
class LPDDR5Constraint(SignalConstraint["LPDDR5"]):
    """Signal Integrity Constraint for LPDDR5

    Args:
        width: Channel width
        rank: Rank configuration
        params: Constraint parameters
        diff_structure: Differential routing structure
        se_structure: Single-ended routing structure
    """

    def __init__(
        self,
        width: LPDDR5Width,
        rank: LPDDR5Rank,
        params: LPDDR5ConstraintParams | None = None,
        diff_structure: DifferentialRoutingStructure | None = None,
        se_structure: RoutingStructure | None = None,
    ):
        super().__init__()
        self.width = width
        self.rank = rank
        self.params = params or LPDDR5ConstraintParams()

        if not diff_structure:
            diff_structure = current.substrate.differential_routing_structure(
                Toleranced.percent(100, 5)
            )
        if not se_structure:
            se_structure = current.substrate.routing_structure(Toleranced.percent(50, 5))

        self.ck_constraint = DiffPairConstraint(
            skew=self.params.skew_ck, loss=self.params.loss, structure=diff_structure
        )
        self.wck_constraint = DiffPairConstraint(
            skew=self.params.skew_wck, loss=self.params.loss, structure=diff_structure
        )
        self.rdqs_constraint = DiffPairConstraint(
            skew=self.params.skew_rdqs, loss=self.params.loss, structure=diff_structure
        )
        self.se_structure = se_structure

    def constrain(self, src: LPDDR5, dst: LPDDR5):
        """Apply all LPDDR5 constraints

        Args:
            src: Source LPDDR5 port
            dst: Destination LPDDR5 port
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

            # CS and CA timing relative to CK
            for rank_idx in range(nr):
                cs_topo = Topology(src.cs[ch_idx][rank_idx], dst.cs[ch_idx][rank_idx])
                self.add(
                    ConstrainReferenceDifference(guide_ck, [cs_topo]).timing_difference(
                        self.params.skew_ck_cs
                    )
                )
                cs_constrained = Constrain(cs_topo).insertion_loss(self.params.loss)
                cs_constrained.structure(self.se_structure)
                self.add(cs_constrained)

            for ca_bit in range(7):
                ca_topo = Topology(src.ca[ch_idx][ca_bit], dst.ca[ch_idx][ca_bit])
                self.add(
                    ConstrainReferenceDifference(guide_ck, [ca_topo]).timing_difference(
                        self.params.skew_ck_ca
                    )
                )
                ca_constrained = Constrain(ca_topo).insertion_loss(self.params.loss)
                ca_constrained.structure(self.se_structure)
                self.add(ca_constrained)

            # Constrain data lanes (2 per channel)
            for lane_idx in range(2):
                src_lane = src.d[ch_idx][lane_idx]
                dst_lane = dst.d[ch_idx][lane_idx]

                # WCK and RDQS constraints
                self.wck_constraint.constrain(src_lane.wck, dst_lane.wck)
                self.rdqs_constraint.constrain(src_lane.rdqs, dst_lane.rdqs)

                guide_wck = Topology(src_lane.wck.p, dst_lane.wck.p)
                guide_rdqs = Topology(src_lane.rdqs.p, dst_lane.rdqs.p)

                # CK to WCK/RDQS timing
                self.add(
                    ConstrainReferenceDifference(guide_ck, [guide_wck]).timing_difference(
                        self.params.skew_ck_wck
                    )
                )
                self.add(
                    ConstrainReferenceDifference(guide_ck, [guide_rdqs]).timing_difference(
                        self.params.skew_ck_rdqs
                    )
                )

                # DQ and DMI constraints
                for src_dq, dst_dq in zip(src_lane.dq, dst_lane.dq, strict=True):
                    dq_topo = Topology(src_dq, dst_dq)
                    # Timing to both WCK and RDQS
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
                    dq_constrained = Constrain(dq_topo).insertion_loss(self.params.loss)
                    dq_constrained.structure(self.se_structure)
                    self.add(dq_constrained)

                # DMI constraints
                dmi_topo = Topology(src_lane.dmi, dst_lane.dmi)
                self.add(
                    ConstrainReferenceDifference(guide_wck, [dmi_topo]).timing_difference(
                        self.params.skew_wck_dq
                    )
                )
                dmi_constrained = Constrain(dmi_topo).insertion_loss(self.params.loss)
                dmi_constrained.structure(self.se_structure)
                self.add(dmi_constrained)

        # Reset signal (shared across all channels)
        reset_topo = Topology(src.reset_n, dst.reset_n)
        reset_constrained = Constrain(reset_topo).insertion_loss(self.params.loss)
        reset_constrained.structure(self.se_structure)
        self.add(reset_constrained)
