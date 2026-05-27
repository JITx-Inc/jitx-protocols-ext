"""JESD204 Protocol

JESD204 is a high-speed serial interface standard for data converters (ADCs/DACs)
connecting to logic devices (FPGAs/ASICs).
https://en.wikipedia.org/wiki/JESD204

This module supports defining JESD204B and JESD204C connections between
converters and logic devices on a printed circuit board.

## JESD204 Versions

- **JESD204A**: Up to 3.125 Gbps per lane, frame clock based
- **JESD204B**: Up to 12.5 Gbps per lane, 8B/10B encoding, SYSREF for
  deterministic latency (Subclass 1), up to 32 lanes per link
- **JESD204C**: Up to 32.5 Gbps per lane, adds 64B/66B encoding (eliminates
  SYNC~ pin), backward compatible with JESD204B 8B/10B mode

## Signal Architecture

Unlike bidirectional protocols (SATA, PCIe), JESD204 data lanes are
**unidirectional**: all lanes in a link flow in the same direction
(converter TX → logic device RX for ADCs, logic device TX → converter RX
for DACs). Each lane is a single CML differential pair.

Control and clock signals:

- **SYNC~**: LVDS differential pair from receiver to transmitter, initiates
  lane alignment. Eliminated in JESD204C 64B/66B mode.
- **SYSREF**: LVDS system reference for deterministic latency (Subclass 1 only).
- **DEVCLK**: Differential device clock distributed to all devices.

## Subclasses (JESD204B/C)

- **Subclass 0**: No deterministic latency (backward compatible), no SYSREF
- **Subclass 1**: Deterministic latency via SYSREF signal
- **Subclass 2**: Deterministic latency via SYNC~ (no SYSREF)

## DC Coupling

JESD204 uses DC-coupled CML signaling for data lanes. Unlike PCIe or SATA,
AC coupling capacitors are typically NOT required on data lanes.

## References

- https://www.analog.com/en/lp/001/jesd204-serial-interface-jedec-standard-data-converters.html
- https://wiki.analog.com/resources/fpga/peripherals/jesd204
- https://www.analog.com/media/en/technical-documentation/technical-articles/JESD204B-Survival-Guide.pdf
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from jitx import current
from jitx.net import DiffPair, Port
from jitx.si import (
    ConstrainReferenceDifference,
    DifferentialRoutingStructure,
    DiffPairConstraint,
    SignalConstraint,
    Topology,
)
from jitx.toleranced import Toleranced


class JESD204LaneCount(Enum):
    """JESD204 Lane Count Specifications

    Standard JESD204 link widths. The specification supports up to 32 lanes,
    but most devices use 1, 2, 4, or 8.
    """

    x1 = 1
    "1 lane"
    x2 = 2
    "2 lanes"
    x4 = 4
    "4 lanes"
    x8 = 8
    "8 lanes"
    x16 = 16
    "16 lanes"
    x32 = 32
    "32 lanes"


class JESD204(Port):
    """JESD204 Bundle

    Complete JESD204B/C interface with unidirectional data lanes and optional
    control/clock signals.

    Data lanes are unidirectional CML differential pairs (100 ohm). Unlike
    SATA/PCIe which use LanePair (TX+RX per lane), each JESD204 lane is a
    single DiffPair flowing in one direction.

    Args:
        lane_count: Number of data lanes (1-32)
        include_sync: Include SYNC~ signal (set False for JESD204C 64B/66B mode)
        include_sysref: Include SYSREF signal (set False for Subclass 0 or 2)
        include_devclk: Include DEVCLK signal

    Attributes:
        lane: Array of unidirectional data lane differential pairs
        SYNC: Sync signal differential pair (None if not included)
        SYSREF: System reference differential pair (None if not included)
        DEVCLK: Device clock differential pair (None if not included)
    """

    lane: Sequence[DiffPair]
    "Unidirectional data lane differential pairs"

    SYNC: DiffPair | None = None
    "Synchronization signal (LVDS, receiver to transmitter)"

    SYSREF: DiffPair | None = None
    "System reference for deterministic latency (LVDS, Subclass 1)"

    DEVCLK: DiffPair | None = None
    "Device clock (differential)"

    def __init__(
        self,
        lane_count: JESD204LaneCount | int = JESD204LaneCount.x4,
        include_sync: bool = True,
        include_sysref: bool = True,
        include_devclk: bool = True,
    ):
        count = lane_count.value if isinstance(lane_count, JESD204LaneCount) else lane_count
        self.lane = tuple(DiffPair() for _ in range(count))
        if include_sync:
            self.SYNC = DiffPair()
        if include_sysref:
            self.SYSREF = DiffPair()
        if include_devclk:
            self.DEVCLK = DiffPair()


@dataclass(frozen=True)
class JESD204Standard:
    """JESD204 Standard Parameters

    Attributes:
        skew: Allowed intra-pair skew in seconds
        lane_skew: Maximum skew between all lanes in a link
        loss: Allowed loss in dB
        impedance: Differential impedance
    """

    skew: Toleranced
    "Intra-pair skew specification"

    lane_skew: Toleranced
    "Inter-lane skew specification"

    loss: float
    "Allowed loss in dB"

    impedance: Toleranced
    "Differential trace impedance"


class JESD204Version(Enum):
    """JESD204 Version Specifications

    Different JESD204 versions with accompanying standard values.
    To customize parameters, use :py:func:`dataclasses.replace`.

    Example:
        >>> import dataclasses
        >>> custom = dataclasses.replace(JESD204Version.JESD204B.value, loss=10.0)
    """

    JESD204B = JESD204Standard(
        skew=Toleranced(0, 1.0e-12),
        lane_skew=Toleranced(0, 100.0e-12),
        loss=12.0,
        impedance=Toleranced.percent(100, 20),
    )
    "Up to 12.5 Gbps per lane, 8B/10B encoding"

    JESD204C = JESD204Standard(
        skew=Toleranced(0, 0.5e-12),
        lane_skew=Toleranced(0, 50.0e-12),
        loss=15.0,
        impedance=Toleranced.percent(100, 15),
    )
    "Up to 32.5 Gbps per lane, 64B/66B encoding"

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


class JESD204Constraint(SignalConstraint["JESD204"]):
    """Signal Integrity Constraint for JESD204

    This constraint applies intra-pair skew, inter-lane skew, and loss limits
    to JESD204 connections. Data lanes, SYNC~, SYSREF, and DEVCLK are all
    constrained when present.

    Args:
        standard: JESD204 version specification containing skew and loss parameters
        structure: Differential routing structure. If not provided, uses substrate default.
    """

    def __init__(
        self,
        standard: JESD204Standard,
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

    def constrain(self, src: JESD204, dst: JESD204):
        """Apply constraints to JESD204 connection

        Data lanes are constrained directly (src.lane[i] to dst.lane[i])
        since they are unidirectional differential pairs.

        Args:
            src: Source JESD204 port (transmitter side)
            dst: Destination JESD204 port (receiver side)

        Raises:
            ValueError: If source and destination have mismatched lane counts
            ValueError: If source and destination have mismatched signal presence
        """
        if len(src.lane) != len(dst.lane):
            raise ValueError(
                f"Mismatched lane count: src has {len(src.lane)} lanes, "
                f"dst has {len(dst.lane)} lanes"
            )

        # Constrain each data lane (unidirectional: src → dst)
        for src_lane, dst_lane in zip(src.lane, dst.lane, strict=True):
            self.diffpair_constraint.constrain(src_lane, dst_lane)

        # Inter-lane skew constraints for multi-lane links
        if len(src.lane) > 1:
            ref_topo = Topology(src.lane[0].p, dst.lane[0].p)

            other_topos = [
                Topology(src_lane.p, dst_lane.p)
                for src_lane, dst_lane in zip(src.lane[1:], dst.lane[1:], strict=True)
            ]

            self.add(
                ConstrainReferenceDifference(
                    ref_topo, other_topos
                ).timing_difference(self.lane_skew)
            )

        # Constrain SYNC~ if present on both sides
        if src.SYNC is not None and dst.SYNC is not None:
            self.diffpair_constraint.constrain(dst.SYNC, src.SYNC)
        elif (src.SYNC is None) != (dst.SYNC is None):
            raise ValueError(
                "Mismatched SYNC presence: both endpoints must have SYNC or neither"
            )

        # Constrain SYSREF if present on both sides
        if src.SYSREF is not None and dst.SYSREF is not None:
            self.diffpair_constraint.constrain(src.SYSREF, dst.SYSREF)
        elif (src.SYSREF is None) != (dst.SYSREF is None):
            raise ValueError(
                "Mismatched SYSREF presence: both endpoints must have SYSREF or neither"
            )

        # Constrain DEVCLK if present on both sides
        if src.DEVCLK is not None and dst.DEVCLK is not None:
            self.diffpair_constraint.constrain(src.DEVCLK, dst.DEVCLK)
        elif (src.DEVCLK is None) != (dst.DEVCLK is None):
            raise ValueError(
                "Mismatched DEVCLK presence: both endpoints must have DEVCLK or neither"
            )
