"""PCIe Protocol

PCI Express is a serial communication protocol supporting high speed data links.
https://en.wikipedia.org/wiki/PCI_Express

This module supports defining PCIe connections between components in a board design.

## PCIe Blocking Capacitors

The PCIe specification calls for AC coupling for the data lanes. This is typically
achieved using a blocking capacitor. When connecting two active components, this
typically means blocking caps from Tx -> Rx on both sides of the link. When
connecting an active component to a passive component, this typically means adding
the blocking caps only on the Tx -> Rx side of the link.

Use the :py:meth:`~jitx.si.SignalConstraint.constrain_topology` mechanism to add
blocking capacitors to the topology.

## PCIe Variants

This module supports both **card edge** and **on-board** PCIe connections:

- **Card Edge**: Full PCIe with control signals (PEWAKE#, PERST#, CLKREQ#, PRSNT#)
  for expansion cards and connectors
- **On-Board**: Data-only PCIe without control signals for direct chip-to-chip
  connections on the same board (also optional refclk)

## References

- https://pcisig.com/pci-express%C2%AE-50-architecture-channel-insertion-loss-budget-0
- https://docs.broadcom.com/doc/pcie-pcb-layout-review
- https://community.nxp.com/pwmxy87654/attachments/pwmxy87654/powerquicc/2284/1/AN307_TP_HARDWARE_DESIGN_PCI_SMGIII.pdf
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from jitx import current
from jitx.common import LanePair
from jitx.net import DiffPair, Port
from jitx.si import DifferentialRoutingStructure, DiffPairConstraint, SignalConstraint
from jitx.toleranced import Toleranced


class PCIeWidth(Enum):
    """PCIe Lane Width Specifications

    Standard PCIe link widths.
    """

    x1 = 1
    "PCIe x1 - 1 lane"
    x2 = 2
    "PCIe x2 - 2 lanes"
    x4 = 4
    "PCIe x4 - 4 lanes"
    x8 = 8
    "PCIe x8 - 8 lanes"
    x16 = 16
    "PCIe x16 - 16 lanes"
    x32 = 32
    "PCIe x32 - 32 lanes"


class PCIeData(Port):
    """PCIe Data Bundle

    The data bundle consists of a configurable number of lane pairs (RX/TX pairs)
    and an optional refclk (100MHz) differential pair.

    Args:
        width: PCIe lane width (x1, x2, x4, x8, x16, or x32)
        include_refclk: If True (default), include refclk. Set to False for
                        on-board connections where the devices don't use this clock signal.

    Attributes:
        lane: Array of lane pairs for data transfer
        refclk: 100MHz reference clock differential pair (None for on-board)
    """

    lane: Sequence[LanePair]
    "Lane pairs for PCIe data transfer"

    refclk: DiffPair | None = None
    "100MHz reference clock (None for on-board connections)"

    def __init__(self, width: PCIeWidth = PCIeWidth.x1, include_refclk: bool = True):
        self.lane = tuple(LanePair() for _ in range(width.value))
        if include_refclk:
            self.refclk = DiffPair()


class PCIeControl(Port):
    """PCIe Control Bundle

    Control signals for PCIe card edge connections.

    Args:
        prsnt: Include PRSNT# signal for hot plug detection

    Attributes:
        PEWAKE: Power event wake signal
        PERST: PCIe reset signal
        CLKREQ: Clock request signal
        PRSNT: Optional hot plug detection signal
    """

    PEWAKE = Port()
    "Power event wake signal"

    PERST = Port()
    "PCIe reset signal"

    CLKREQ = Port()
    "Clock request signal"

    PRSNT: Port | None = None
    "Hot plug detection signal (optional)"

    def __init__(self, prsnt: bool = False):
        if prsnt:
            self.PRSNT = Port()


class PCIe(Port):
    """PCIe Bundle

    Complete PCIe bundle with data and optional control channels.

    Args:
        width: PCIe lane width (x1, x2, x4, x8, x16, or x32)
        on_board: If True, omits control signals and refclk for on-board connections
                  (board-to-board where each device has its own clock source).
                  If False (default), includes control signals and refclk for card edge.
        prsnt: Include PRSNT# signal (only applicable when on_board=False)

    Attributes:
        data: PCIe data channel (lanes + optional refclk)
        control: PCIe control channel (only present when on_board=False)
    """

    data: PCIeData
    "Data channel for PCIe"

    control: PCIeControl | None = None
    "Control channel for PCIe (card edge only)"

    def __init__(
        self, width: PCIeWidth = PCIeWidth.x1, on_board: bool = False, prsnt: bool = False
    ):
        # On-board connections don't have refclk (each device has its own clock)
        self.data = PCIeData(width, include_refclk=not on_board)
        if not on_board:
            self.control = PCIeControl(prsnt=prsnt)


@dataclass(frozen=True)
class PCIeStandard:
    """PCIe Standard Parameters

    Attributes:
        skew: Allowed intra-pair skew in seconds
        loss: Allowed loss in dB
        impedance: Differential impedance
    """

    skew: Toleranced
    "Intra-pair skew specification"

    loss: float
    "Allowed loss in dB"

    impedance: Toleranced
    "Differential trace impedance"


class PCIeVersion(Enum):
    """PCIe Version Specifications

    Different PCIe generations with accompanying standard values.
    To customize parameters, use :py:func:`dataclasses.replace`.

    Example:
        >>> import dataclasses
        >>> custom = dataclasses.replace(PCIeVersion.V3.value, loss=12.0)
    """

    V1 = PCIeStandard(Toleranced(0, 1.0e-12), 12.0, Toleranced.percent(100, 5))
    "2.5 GT/s"

    V2 = PCIeStandard(Toleranced(0, 1.0e-12), 12.0, Toleranced.percent(100, 5))
    "5.0 GT/s"

    V3 = PCIeStandard(Toleranced(0, 1.0e-12), 10.3, Toleranced.percent(85, 5))
    "8.0 GT/s"

    V4 = PCIeStandard(Toleranced(0, 0.850e-12), 13.5, Toleranced.percent(85, 5))
    "16.0 GT/s"

    V5 = PCIeStandard(Toleranced(0, 0.850e-12), 16.0, Toleranced.percent(85, 5))
    "32.0 GT/s"

    V6 = PCIeStandard(Toleranced(0, 0.850e-12), 16.0, Toleranced.percent(85, 5))
    "64.0 GT/s"

    V7 = PCIeStandard(Toleranced(0, 0.850e-12), 16.0, Toleranced.percent(85, 5))
    "128.0 GT/s"

    @property
    def skew(self) -> Toleranced:
        return self.value.skew

    @property
    def loss(self) -> float:
        return self.value.loss

    @property
    def impedance(self) -> Toleranced:
        return self.value.impedance


class PCIeConstraint(SignalConstraint["PCIe"]):
    """Signal Integrity Constraint for PCIe

    This constraint applies intra-pair skew and loss limits to PCIe connections.
    All lane pairs and the refclk are constrained.

    Args:
        standard: PCIe version specification containing skew and loss parameters
        structure: Differential routing structure. If not provided, uses substrate default.
    """

    def __init__(
        self,
        standard: PCIeStandard,
        structure: DifferentialRoutingStructure | None = None,
        xover: bool = False
    ):
        if not structure:
            self.structure = current.substrate.differential_routing_structure(
                standard.impedance
            )
        else :
            self.structure = structure
        self.xover = xover
        self.diffpair_constraint = DiffPairConstraint(
            skew=standard.skew, loss=standard.loss, structure=self.structure
        )

    def constrain(self, src: PCIe, dst: PCIe):
        """Apply constraints to PCIe connection

        Args:
            src: Source PCIe port
            dst: Destination PCIe port

        Raises:
            ValueError: If source and destination have mismatched lane counts
            ValueError: If source and destination have mismatched refclk presence
        """
        if len(src.data.lane) != len(dst.data.lane):
            raise ValueError(
                f"Mismatched lane count: src has {len(src.data.lane)} lanes, "
                f"dst has {len(dst.data.lane)} lanes"
            )

        # Constrain each lane pair (TX and RX for each lane)
        for self.src_lane, self.dst_lane in zip(src.data.lane, dst.data.lane, strict=True):
            if not self.xover:
                self.diffpair_constraint.constrain(self.src_lane.TX, self.dst_lane.TX)
                self.diffpair_constraint.constrain(self.src_lane.RX, self.dst_lane.RX)
            else:
                # Constrain TX->RX path
                self.diffpair_constraint.constrain(self.src_lane.TX, self.dst_lane.RX)
                # Constrain RX<-TX path
                self.diffpair_constraint.constrain(self.src_lane.RX, self.dst_lane.TX)

        # Constrain refclk if present on both sides
        if src.data.refclk is not None and dst.data.refclk is not None:
            self.diffpair_constraint.constrain(src.data.refclk, dst.data.refclk)
        elif (src.data.refclk is None) != (dst.data.refclk is None):
            raise ValueError(
                "Mismatched refclk presence: both endpoints must have refclk or neither"
            )

def connect_pcie_null_modem(a: PCIe, b: PCIe):
    """Connect two PCIe bundles with TX-to-RX crossover.

    Creates null-modem style connections between two active PCIe devices where
    TX lanes connect to RX lanes and vice versa. This is the standard way to
    connect two active PCIe devices on the same board.

    The function connects:
    - a.data.lane[i].TX to b.data.lane[i].RX
    - a.data.lane[i].RX to b.data.lane[i].TX
    - a.data.refclk to b.data.refclk (straight-through, if present)
    - a.control to b.control (straight-through, if present)

    Args:
        a: First PCIe port
        b: Second PCIe port

    Raises:
        ValueError: If the two ports have mismatched lane counts
        ValueError: If the two ports have mismatched refclk presence

    Example:
        >>> class PCIeLink(Circuit):
        ...     cpu_pcie = PCIe(PCIeWidth.x4, on_board=True)
        ...     switch_pcie = PCIe(PCIeWidth.x4, on_board=True)
        ...
        ...     def __init__(self):
        ...         # Connect CPU to switch with proper TX->RX crossover
        ...         connect_pcie_crossover(self.cpu_pcie, self.switch_pcie)
    """
    if len(a.data.lane) != len(b.data.lane):
        raise ValueError(
            f"Mismatched lane count: a has {len(a.data.lane)} lanes, "
            f"b has {len(b.data.lane)} lanes"
        )
    conns = []
    # Connect lanes with TX->RX crossover
    for lane_a, lane_b in zip(a.data.lane, b.data.lane, strict=True):
        conns.append([lane_a.TX >> lane_b.RX])
        conns.append([lane_a.RX >> lane_b.TX])

    # Connect refclk straight-through if present on both sides
    if a.data.refclk is not None and b.data.refclk is not None:
        conns.append([a.data.refclk >> b.data.refclk])
    elif (a.data.refclk is None) != (b.data.refclk is None):
        raise ValueError(
            "Mismatched refclk presence: both endpoints must have refclk or neither"
        )

    # Connect control signals straight-through if present on both sides
    if a.control is not None and b.control is not None:
        conns.append([a.control >> b.control])

    return conns
