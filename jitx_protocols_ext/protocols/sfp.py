"""(Q)SFP Protocol

SFP is a serial communication protocol supporting high speed links for networking
applications based on SERDES (RX/TX) data pairs.

https://en.wikipedia.org/wiki/Small_Form-factor_Pluggable

This module supports defining SFP, QSFP, QSFP-DD links between sources and
receivers on a printed circuit board.

## SFP Variants

| Name       | Nominal speed | Lanes | Standard         |
|------------|---------------|-------|------------------|
| SFP        | 1 Gbit/s      | 1     | SFF INF-8074i    |
| cSFP       | 1 Gbit/s      | 2     |                  |
| SFP+       | 10 Gbit/s     | 1     | SFF SFF-8431 4.1 |
| SFP28      | 25 Gbit/s     | 1     | SFF SFF-8402     |
| SFP56      | 50 Gbit/s     | 1     |                  |
| SFP-DD     | 100 Gbit/s    | 2     | SFP-DD MSA       |
| SFP112     | 100 Gbit/s    | 1     |                  |
| SFP-DD112  | 200 Gbit/s    | 2     |                  |
| QSFP       | 4 Gbit/s      | 4     | SFF INF-8438     |
| QSFP+      | 40 Gbit/s     | 4     | SFF SFF-8436     |
| QSFP28     | 100 Gbit/s    | 4     | SFF SFF-8665     |
| QSFP56     | 200 Gbit/s    | 4     | SFF SFF-8665     |
| QSFP112    | 400 Gbit/s    | 4     | SFF SFF-8665     |
| QSFP-DD    | 400 Gbit/s    | 8     | SFF INF-8628     |
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from jitx import current
from jitx.common import LanePair
from jitx.container import inner
from jitx.net import Port
from jitx.si import (
    ConstrainReferenceDifference,
    DifferentialRoutingStructure,
    DiffPairConstraint,
    SignalConstraint,
    Topology,
)
from jitx.toleranced import Toleranced


class SFP_Lane(Port):
    """SFP Lane Bundle

    This bundle is used to represent a single SFP, SFP-DD, QSFP, or QSFP-DD link.

    Args:
        lane_count: Number of lanes (1, 2, 4, or 8)

    Attributes:
        lanes: Array of lane pairs for data transfer
    """

    lanes: Sequence[LanePair]
    "Array of lane pairs"

    def __init__(self, lane_count: int):
        self.lanes = tuple(LanePair() for _ in range(lane_count))


# Convenience functions for standard configurations
def SFP() -> SFP_Lane:
    """Single SFP link (1 lane)

    The SFP link is a high speed signaling protocol based on 1 SERDES (RX/TX)
    data pair (aka lane).
    """
    return SFP_Lane(1)


def SFP_DD() -> SFP_Lane:
    """SFP Dual Density link (2 lanes)

    The SFP-DD link is a high speed signaling protocol based on 2 SERDES (RX/TX)
    data pairs (aka lanes).
    """
    return SFP_Lane(2)


def QSFP() -> SFP_Lane:
    """Quad SFP link (4 lanes)

    The QSFP link is a high speed signaling protocol based on 4 SERDES (RX/TX)
    data pairs (aka lanes).
    """
    return SFP_Lane(4)


def QSFP_DD() -> SFP_Lane:
    """Quad SFP Dual Density link (8 lanes)

    The QSFP-DD link is a high speed signaling protocol based on 8 SERDES (RX/TX)
    data pairs (aka lanes).
    """
    return SFP_Lane(8)


@dataclass(frozen=True)
class SFPStandard:
    """SFP Standard Parameters

    Attributes:
        lane_count: Number of lanes for this link type
        skew: Allowed intra-pair skew in seconds
        lane_skew: Maximum skew between all lanes in a link
        loss: Allowed loss in dB
        impedance: Differential impedance (100Ω ±10%)
    """

    lane_count: int
    "Number of lanes in this SFP link type"

    skew: Toleranced
    "Intra-pair skew specification"

    lane_skew: Toleranced
    "Inter-lane skew specification"

    loss: float
    "Allowed loss in dB"

    impedance: Toleranced
    "Differential trace impedance"


_SFP_SKEW = Toleranced(0, 1.0e-12)
_SFP_LANE_SKEW = Toleranced(0, 100.0e-12)
_SFP_LOSS = 5.0
_SFP_IMPEDANCE = Toleranced.percent(100, 10)


def _sfp_std(lanes: int) -> SFPStandard:
    return SFPStandard(lanes, _SFP_SKEW, _SFP_LANE_SKEW, _SFP_LOSS, _SFP_IMPEDANCE)


class SFPLink(Enum):
    """SFP Link Type Specifications

    Different SFP variants with accompanying standard values.
    Each enum member is an SFPStandard instance.

    Example:
        >>> import dataclasses
        >>> custom = dataclasses.replace(SFPLink.SFP_PLUS.value, loss=6.0)
    """

    SFP = _sfp_std(1)
    "1.0 Gbit/s - 1 lane"

    CSFP = _sfp_std(2)
    "1.0 Gbit/s - 2 lanes (cSFP)"

    SFP_PLUS = _sfp_std(1)
    "10.0 Gbit/s - 1 lane (SFP+)"

    SFP28 = _sfp_std(1)
    "25.0 Gbit/s - 1 lane"

    SFP56 = _sfp_std(1)
    "50.0 Gbit/s - 1 lane"

    SFP_DD = _sfp_std(2)
    "100.0 Gbit/s - 2 lanes (SFP-DD)"

    SFP112 = _sfp_std(1)
    "100.0 Gbit/s - 1 lane"

    SFP_DD112 = _sfp_std(2)
    "200.0 Gbit/s - 2 lanes (SFP-DD112)"

    QSFP = _sfp_std(4)
    "4.0 Gbit/s - 4 lanes"

    QSFP_PLUS = _sfp_std(4)
    "40.0 Gbit/s - 4 lanes (QSFP+)"

    QSFP28 = _sfp_std(4)
    "100.0 Gbit/s - 4 lanes"

    QSFP56 = _sfp_std(4)
    "200.0 Gbit/s - 4 lanes"

    QSFP112 = _sfp_std(4)
    "400.0 Gbit/s - 4 lanes"

    QSFP_DD = _sfp_std(8)
    "400.0 Gbit/s - 8 lanes (QSFP-DD)"

    @property
    def skew(self) -> Toleranced:
        return self.value.skew

    @property
    def lane_skew(self) -> Toleranced:
        return self.value.lane_skew

    @property
    def loss(self) -> float:
        return self.value.loss

    @property
    def impedance(self) -> Toleranced:
        return self.value.impedance


def link_to_lane_count(link: SFPLink) -> int:
    """Helper function to get the number of lanes for a given SFP link type

    Args:
        link: SFP link type

    Returns:
        Number of lanes for the specified link type
    """
    return link.value.lane_count


@inner
class SFPConstraint(SignalConstraint["SFP_Lane"]):
    """Signal Integrity Constraint for SFP

    This constraint applies intra-pair skew, inter-lane skew, and loss limits
    to SFP connections.

    Args:
        standard: SFP standard specification containing skew and loss parameters
        structure: Differential routing structure. If not provided, uses substrate default.
    """

    def __init__(
        self,
        standard: SFPStandard,
        structure: DifferentialRoutingStructure | None = None,
    ):
        super().__init__()
        if not structure:
            structure = current.substrate.differential_routing_structure(
                standard.impedance
            )
        self.diffpair_constraint = DiffPairConstraint(
            skew=standard.skew, loss=standard.loss, structure=structure
        )
        self.lane_skew = standard.lane_skew

    def constrain(self, src: SFP_Lane, dst: SFP_Lane):
        """Apply constraints to SFP connection

        Args:
            src: Source SFP port
            dst: Destination SFP port

        Raises:
            ValueError: If source and destination have mismatched lane counts
        """
        if len(src.lanes) != len(dst.lanes):
            raise ValueError(
                f"Mismatched lane count: src has {len(src.lanes)} lanes, "
                f"dst has {len(dst.lanes)} lanes"
            )

        # Constrain each lane pair (TX and RX for each lane)
        for src_lane, dst_lane in zip(src.lanes, dst.lanes, strict=True):
            # Constrain TX path (src TX -> dst RX)
            self.diffpair_constraint.constrain(src_lane.TX, dst_lane.RX)
            # Constrain RX path (src RX <- dst TX)
            self.diffpair_constraint.constrain(src_lane.RX, dst_lane.TX)

        # Inter-lane skew constraints are applied between all lanes
        # This ensures all lanes arrive within the lane_skew window
        if len(src.lanes) > 1:
            # Use the first TX lane as the reference for timing
            ref_tx_topo = Topology(src.lanes[0].TX.p, dst.lanes[0].RX.p)

            # Create topologies for all other TX lanes
            other_tx_topos = [
                Topology(src_lane.TX.p, dst_lane.RX.p)
                for src_lane, dst_lane in zip(src.lanes[1:], dst.lanes[1:], strict=True)
            ]

            # Add inter-lane timing constraint
            self.add(
                ConstrainReferenceDifference(
                    ref_tx_topo, other_tx_topos
                ).timing_difference(self.lane_skew)
            )

            # Do the same for RX lanes
            ref_rx_topo = Topology(src.lanes[0].RX.p, dst.lanes[0].TX.p)
            other_rx_topos = [
                Topology(src_lane.RX.p, dst_lane.TX.p)
                for src_lane, dst_lane in zip(src.lanes[1:], dst.lanes[1:], strict=True)
            ]

            self.add(
                ConstrainReferenceDifference(
                    ref_rx_topo, other_rx_topos
                ).timing_difference(self.lane_skew)
            )
