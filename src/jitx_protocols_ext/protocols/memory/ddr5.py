"""DDR5 Memory Protocol

DDR5 is the current-generation high-speed memory standard.
https://en.wikipedia.org/wiki/DDR5_SDRAM

The functions and definitions in this file support defining DDR5 connections between
microprocessors and memories in a board design. DDR5 introduces significant
architectural changes over DDR4, including sub-channel architecture, a unified 14-bit
Command/Address (CA) bus using PODL signaling, on-die ECC, and Decision Feedback
Equalization (DFE).

This implementation is based on JEDEC JESD79-5 (DDR5 SDRAM Standard).

## Key Differences from DDR4

1. Sub-channel architecture: Two independent 32-bit sub-channels per DIMM
2. Unified 14-bit CA bus replaces separate A/BA/BG/ACT_n/PAR signals
3. PODL (Pseudo Open-Drain Logic) signaling for CA bus
4. Lower impedances: 80Ω differential CK/DQS, 40Ω single-ended DQ/CA
5. Tighter timing constraints: ±0.5ps intra-pair skew (vs DDR4's ±1.0ps)

## DDR5 Timing Constraints

1. CK intra-pair skew: ±0.5ps
2. DQS intra-pair skew: ±0.5ps
3. DQ to DQS skew within byte lane: ±2.5ps
4. DMI to DQS skew within byte lane: ±2.5ps
5. CA to CK skew: ±15ps
6. CA intra-group skew: ±8ps
7. CK.P to DQS.P cross-channel: -85ps to +935ps
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
    DifferentialRoutingStructure,
    DiffPairConstraint,
    RoutingStructure,
    SignalConstraint,
    Topology,
)
from jitx.toleranced import Toleranced


class DDR5Width(Enum):
    """DDR5 Channel Width

    Common lane widths for DDR5 memory channels (number of DQ signals).
    DDR5 uses sub-channel architecture with 32-bit sub-channels.
    """

    x8 = 8
    "8 bit width (single x8 DRAM device)"
    x16 = 16
    "16 bit width (single x16 DRAM device)"
    x32 = 32
    "32 bit width (one sub-channel, non-ECC)"
    x40 = 40
    "40 bit width (one sub-channel with ECC)"
    x64 = 64
    "64 bit width (full DIMM, non-ECC)"
    x72 = 72
    "72 bit width (full DIMM with ECC)"


def width_to_int(width: DDR5Width) -> int:
    """Convert DDR5 width enum to integer bit width

    Args:
        width: DDR5 width enum

    Returns:
        Number of DQ bits
    """
    return width.value


def width_to_lane_count(width: DDR5Width) -> int:
    """Convert DDR5 width to number of byte lanes (DQS pairs)

    Each byte lane is 8 bits and has one DQS pair and one DMI signal.

    Args:
        width: DDR5 width enum

    Returns:
        Number of 8-bit byte lanes (DQS pairs)
    """
    if width == DDR5Width.x8:
        return 1
    if width == DDR5Width.x16:
        return 2
    if width == DDR5Width.x32:
        return 4
    if width == DDR5Width.x40:
        return 5  # 4 data + 1 ECC
    if width == DDR5Width.x64:
        return 8
    if width == DDR5Width.x72:
        return 9  # 8 data + 1 ECC
    raise ValueError(f"Unknown DDR5 width: {width}")


def rank_to_int(rank: DDR5Rank) -> int:
    """Convert DDR5 rank enum to integer count of CS_n signals.

    Args:
        rank: DDR5 rank enum

    Returns:
        Number of CS_n signals
    """
    return rank.value


class DDR5Topology(Enum):
    """DDR5 Topology Type

    Possible topologies for DDR5 memory connections.
    """

    FlyBy = "FlyBy"
    "FlyBy topology (daisy-chain)"


class DDR5Rank(Enum):
    """DDR5 Rank Configuration

    Number of chip select (CS_n) signals.
    """

    SingleRank = 1
    "Single rank - 1 CS_n signal"
    DualRank = 2
    "Dual rank - 2 CS_n signals"
    QuadRank = 4
    "Quad rank - 4 CS_n signals"


class DDR5DataChannel(Port):
    """DDR5 Data Channel Bundle

    Data signals for DDR5 memory.

    Args:
        width: DDR5 channel width

    Attributes:
        DQ: Data bus (width varies: 8 to 72 bits)
        DQS: Data strobe pairs (1 per 8-bit byte lane)
        DMI: Data mask/bus inversion signals (1 per byte lane)
    """

    DQ: Sequence[Port]
    "Data signals"

    DQS: Sequence[DiffPair]
    "Data strobe differential pairs"

    DMI: Sequence[Port]
    "Data mask / bus inversion signals"

    def __init__(self, width: DDR5Width):
        dq_count = width_to_int(width)
        lane_count = width_to_lane_count(width)

        self.DQ = tuple(Port() for _ in range(dq_count))
        self.DQS = tuple(DiffPair() for _ in range(lane_count))
        self.DMI = tuple(Port() for _ in range(lane_count))


class DDR5CAChannel(Port):
    """DDR5 Command/Address Channel Bundle

    Command, address, and control signals for DDR5 memory.
    DDR5 uses a unified 14-bit CA bus with PODL signaling, replacing
    DDR4's separate A/BA/BG/ACT_n/PAR signals.

    DDR5 DRAMs do not have dedicated CKE or ODT pins (unlike DDR4).
    Clock enable is handled via MPC commands on the CA bus, and ODT is
    controlled via mode registers (MR32/MR33) and the CA_ODT strap pin.

    Args:
        rank: Rank configuration (determines CS_n count)

    Attributes:
        CK: Clock differential pair
        CA: Command/Address bus (14 bits: CA[13:0])
        CS_n: Chip select (active low, 1 per rank)
        RESET_n: Reset (active low)
        ALERT_n: Alert (active low)
    """

    CK: DiffPair
    "Clock differential pair"

    CA: Sequence[Port]
    "Command/Address bus CA[13:0]"

    CS_n: Sequence[Port]
    "Chip select (active low)"

    RESET_n = Port()
    "Reset (active low)"

    ALERT_n = Port()
    "Alert (active low)"

    def __init__(self, rank: DDR5Rank):
        rank_count = rank.value

        self.CK = DiffPair()
        self.CA = tuple(Port() for _ in range(14))
        self.CS_n = tuple(Port() for _ in range(rank_count))


class DDR5(Port):
    """DDR5 Memory Bundle

    Complete DDR5 interface combining data and command/address channels.

    Args:
        width: Channel width (x8, x16, x32, x40, x64, x72)
        rank: Rank configuration (SingleRank, DualRank, QuadRank)

    Attributes:
        data: Data channel (DQ, DQS, DMI)
        ca: Command/Address channel (CK, CA, CS_n, RESET_n, ALERT_n)
    """

    data: DDR5DataChannel
    "Data channel"

    ca: DDR5CAChannel
    "Command/Address channel"

    def __init__(
        self,
        width: DDR5Width,
        rank: DDR5Rank = DDR5Rank.SingleRank,
    ):
        self.data = DDR5DataChannel(width)
        self.ca = DDR5CAChannel(rank)


@dataclass(frozen=True)
class DDR5Impedances:
    """DDR5 Impedance Specifications

    Differential and single-ended impedance targets for DDR5 signal groups.
    DDR5 uses lower impedances than DDR4 due to higher speeds and PODL signaling.

    Attributes:
        ck_impedance: CK clock impedance (default: 80Ω ±10%)
        dqs_impedance: DQS strobe impedance (default: 80Ω ±10%)
        dq_impedance: DQ data impedance (default: 40Ω ±10%)
        ca_impedance: Command/Address impedance (default: 40Ω ±10%)
    """

    ck_impedance: Toleranced = Toleranced.percent(80, 10)
    "CK clock differential impedance"

    dqs_impedance: Toleranced = Toleranced.percent(80, 10)
    "DQS strobe differential impedance"

    dq_impedance: Toleranced = Toleranced.percent(40, 10)
    "DQ data single-ended impedance"

    ca_impedance: Toleranced = Toleranced.percent(40, 10)
    "Command/Address single-ended impedance"


@dataclass(frozen=True)
class DDR5DataConstraintParams:
    """DDR5 Data Channel Constraint Parameters

    Timing constraints for the data channel. DDR5 has tighter constraints
    than DDR4 due to higher operating speeds.

    Attributes:
        skew_dqs: DQS intra-pair skew (default: ±0.5ps)
        skew_dq_dqs: DQ to DQS inter-signal skew (default: ±2.5ps)
        skew_dmi_dqs: DMI to DQS timing skew (default: ±2.5ps)
        loss: Maximum loss in dB (default: 5.0dB)
    """

    skew_dqs: Toleranced = Toleranced(0, 0.5e-12)
    "DQS intra-pair skew"

    skew_dq_dqs: Toleranced = Toleranced(0, 2.5e-12)
    "DQ to DQS inter-signal skew"

    skew_dmi_dqs: Toleranced = Toleranced(0, 2.5e-12)
    "DMI to DQS timing skew"

    loss: float = 5.0
    "Maximum loss in dB"


@dataclass(frozen=True)
class DDR5CAConstraintParams:
    """DDR5 Command/Address Constraint Parameters

    Timing constraints for the CA channel.

    Attributes:
        skew_ck: CK intra-pair skew (default: ±0.5ps)
        skew_ca_ck: CA to CK skew (default: ±15ps)
        skew_ca: CA intra-group skew (default: ±8ps)
        loss: Maximum loss in dB (default: 5.0dB)
    """

    skew_ck: Toleranced = Toleranced(0, 0.5e-12)
    "CK intra-pair skew"

    skew_ca_ck: Toleranced = Toleranced(0, 15.0e-12)
    "CA to CK inter-signal skew"

    skew_ca: Toleranced = Toleranced(0, 8.0e-12)
    "CA intra-group skew"

    loss: float = 5.0
    "Maximum loss in dB"


@dataclass(frozen=True)
class DDR5DataCAConstraintParams:
    """DDR5 Data-to-CA Cross-Channel Constraint Parameters

    Timing relationship between data and command/address channels.

    Attributes:
        skew_ck_dqs: CK.P to DQS.P inter-signal skew (default: -85ps to +935ps)
    """

    skew_ck_dqs: Toleranced = Toleranced.min_typ_max(-85.0e-12, 0.0, 935.0e-12)
    "CK.P to DQS.P inter-signal timing skew"


@inner
class DDR5DataConstraint(SignalConstraint["DDR5DataChannel"]):
    """Signal Integrity Constraint for DDR5 Data Channel

    Applies constraints to DQ, DQS, and DMI signals.

    Args:
        params: Data channel constraint parameters
        diff_dqs_structure: Differential routing structure for DQS (80Ω)
        se_dq_structure: Single-ended routing structure for DQ and DMI (40Ω)
    """

    def __init__(
        self,
        params: DDR5DataConstraintParams | None = None,
        diff_dqs_structure: DifferentialRoutingStructure | None = None,
        se_dq_structure: RoutingStructure | None = None,
    ):
        super().__init__()
        self.params = params or DDR5DataConstraintParams()

        if not diff_dqs_structure:
            diff_dqs_structure = current.substrate.differential_routing_structure(
                DDR5Impedances().dqs_impedance
            )
        if not se_dq_structure:
            se_dq_structure = current.substrate.routing_structure(DDR5Impedances().dq_impedance)

        self.dqs_constraint = DiffPairConstraint(
            skew=self.params.skew_dqs, loss=self.params.loss, structure=diff_dqs_structure
        )
        self.se_dq_structure = se_dq_structure

    def constrain(self, src: DDR5DataChannel, dst: DDR5DataChannel):
        """Apply constraints to DDR5 data channel

        Applies per-byte-lane constraints:
        - DQS differential pair skew and loss
        - DQ to DQS timing alignment within each byte lane
        - DMI to DQS timing alignment
        - Single-ended routing structure for DQ and DMI

        Args:
            src: Source data channel
            dst: Destination data channel
        """
        dq_count = len(src.DQ)

        for i, (src_dqs, dst_dqs) in enumerate(zip(src.DQS, dst.DQS, strict=True)):
            self.dqs_constraint.constrain(src_dqs, dst_dqs)

            guide_dqs = Topology(src_dqs.p, dst_dqs.p)

            byte_start = i * 8
            byte_end = min(byte_start + 8, dq_count)

            dq_topos = [Topology(src.DQ[j], dst.DQ[j]) for j in range(byte_start, byte_end)]

            dmi_topo = Topology(src.DMI[i], dst.DMI[i])
            all_data_topos = [*dq_topos, dmi_topo]

            self.add(
                ConstrainReferenceDifference(guide_dqs, all_data_topos).timing_difference(
                    self.params.skew_dq_dqs
                )
            )

            for dq_topo in dq_topos:
                constrained = Constrain(dq_topo).insertion_loss(self.params.loss)
                constrained.structure(self.se_dq_structure)
                self.add(constrained)

            dmi_constrained = Constrain(dmi_topo).insertion_loss(self.params.loss)
            dmi_constrained.structure(self.se_dq_structure)
            self.add(dmi_constrained)


@inner
class DDR5CAConstraint(SignalConstraint["DDR5CAChannel"]):
    """Signal Integrity Constraint for DDR5 Command/Address Channel

    Applies constraints to CK, CA, and control signals.

    Args:
        params: CA channel constraint parameters
        diff_ck_structure: Differential routing structure for CK (80Ω)
        se_structure: Single-ended routing structure for CA and control signals (40Ω)
    """

    def __init__(
        self,
        params: DDR5CAConstraintParams | None = None,
        diff_ck_structure: DifferentialRoutingStructure | None = None,
        se_structure: RoutingStructure | None = None,
    ):
        super().__init__()
        self.params = params or DDR5CAConstraintParams()

        if not diff_ck_structure:
            diff_ck_structure = current.substrate.differential_routing_structure(
                DDR5Impedances().ck_impedance
            )
        if not se_structure:
            se_structure = current.substrate.routing_structure(DDR5Impedances().ca_impedance)

        self.ck_constraint = DiffPairConstraint(
            skew=self.params.skew_ck, loss=self.params.loss, structure=diff_ck_structure
        )
        self.se_structure = se_structure

    def constrain(self, src: DDR5CAChannel, dst: DDR5CAChannel):
        """Apply constraints to DDR5 CA channel

        Applies constraints to:
        - CK differential pair (intra-pair skew)
        - All CA signals relative to CK
        - CA signals relative to each other
        - Control signals (CS_n, RESET_n, ALERT_n) relative to CK
        - Single-ended routing structure and loss

        Args:
            src: Source CA channel
            dst: Destination CA channel
        """
        self.ck_constraint.constrain(src.CK, dst.CK)

        guide_ck = Topology(src.CK.p, dst.CK.p)

        # Use CA[0] as the reference for CA intra-group timing
        guide_ca_group = Topology(src.CA[0], dst.CA[0])

        def constrain_ca_signal(src_sig: Port, dst_sig: Port):
            sig_topo = Topology(src_sig, dst_sig)
            # Timing relative to CK
            self.add(
                ConstrainReferenceDifference(guide_ck, [sig_topo]).timing_difference(
                    self.params.skew_ca_ck
                )
            )
            # Timing relative to CA group
            self.add(
                ConstrainReferenceDifference(guide_ca_group, [sig_topo]).timing_difference(
                    self.params.skew_ca
                )
            )
            # Structure and loss
            constrained = Constrain(sig_topo).insertion_loss(self.params.loss)
            constrained.structure(self.se_structure)
            self.add(constrained)

        # CA bus
        for src_ca, dst_ca in zip(src.CA, dst.CA, strict=True):
            constrain_ca_signal(src_ca, dst_ca)

        # Control signals relative to CK
        for src_cs, dst_cs in zip(src.CS_n, dst.CS_n, strict=True):
            constrain_ca_signal(src_cs, dst_cs)

        constrain_ca_signal(src.RESET_n, dst.RESET_n)
        constrain_ca_signal(src.ALERT_n, dst.ALERT_n)


@inner
class DDR5DataCAConstraint(SignalConstraint["DDR5"]):
    """Signal Integrity Constraint for DDR5 Data-to-CA Cross-Channel Timing

    Constrains the timing relationship between CK and DQS signals across
    the data and command/address channels.

    Args:
        params: Data-to-CA constraint parameters
    """

    def __init__(self, params: DDR5DataCAConstraintParams | None = None):
        super().__init__()
        self.params = params or DDR5DataCAConstraintParams()

    def constrain(self, src: DDR5, dst: DDR5):
        """Apply cross-channel CK-to-DQS timing constraints.

        Constrains each DQS.P signal relative to CK.P with the
        specified timing window (default: -85ps to +935ps).

        Args:
            src: Source DDR5 port
            dst: Destination DDR5 port
        """
        guide_ck = Topology(src.ca.CK.p, dst.ca.CK.p)

        for src_dqs, dst_dqs in zip(src.data.DQS, dst.data.DQS, strict=True):
            target_dqs = Topology(src_dqs.p, dst_dqs.p)
            self.add(
                ConstrainReferenceDifference(guide_ck, [target_dqs]).timing_difference(
                    self.params.skew_ck_dqs
                )
            )


@inner
class DDR5Constraint(SignalConstraint["DDR5"]):
    """Complete DDR5 Signal Integrity Constraint

    Combines data channel, CA channel, and cross-channel constraints.

    When explicit routing structures are provided, they are passed through to
    the sub-constraints. When omitted, the sub-constraints will auto-resolve
    routing structures from ``current.substrate``.

    Args:
        width: DDR5 channel width
        rank: Rank configuration
        topology: Memory topology (default: FlyBy)
        diff_ck_rs: Differential routing structure for CK (80Ω ±10%)
        diff_dqs_rs: Differential routing structure for DQS (80Ω ±10%)
        se_dq_rs: Single-ended routing structure for DQ/DMI (40Ω ±10%)
        se_rs: Single-ended routing structure for CA signals (40Ω ±10%)
        data_constraint: Data channel constraint (overrides diff_dqs_rs/se_dq_rs)
        ca_constraint: CA channel constraint (overrides diff_ck_rs/se_rs)
        data_ca_constraint: Data-to-CA cross-channel constraint
    """

    def __init__(
        self,
        width: DDR5Width,
        rank: DDR5Rank,
        topology: DDR5Topology = DDR5Topology.FlyBy,
        diff_ck_rs: DifferentialRoutingStructure | None = None,
        diff_dqs_rs: DifferentialRoutingStructure | None = None,
        se_dq_rs: RoutingStructure | None = None,
        se_rs: RoutingStructure | None = None,
        data_constraint: SignalConstraint[DDR5DataChannel] | None = None,
        ca_constraint: SignalConstraint[DDR5CAChannel] | None = None,
        data_ca_constraint: SignalConstraint[DDR5] | None = None,
    ):
        super().__init__()
        self.width = width
        self.rank = rank
        self.topology = topology

        if data_constraint is not None:
            self.data_constraint = data_constraint
        else:
            self.data_constraint = DDR5DataConstraint(
                diff_dqs_structure=diff_dqs_rs,
                se_dq_structure=se_dq_rs,
            )

        if ca_constraint is not None:
            self.ca_constraint = ca_constraint
        else:
            self.ca_constraint = DDR5CAConstraint(
                diff_ck_structure=diff_ck_rs,
                se_structure=se_rs,
            )

        self.data_ca_constraint: SignalConstraint[DDR5] = (
            data_ca_constraint if data_ca_constraint is not None else DDR5DataCAConstraint()
        )

    def constrain(self, src: DDR5, dst: DDR5):
        """Apply all DDR5 constraints.

        Applies:
        - Data channel constraints (DQ, DQS, DMI)
        - CA channel constraints (CK, CA, CS_n, RESET_n, ALERT_n)
        - Cross-channel CK-to-DQS timing relationship

        Args:
            src: Source DDR5 port
            dst: Destination DDR5 port
        """
        self.data_constraint.constrain(src.data, dst.data)
        self.ca_constraint.constrain(src.ca, dst.ca)
        self.data_ca_constraint.constrain(src, dst)


def connect_ddr5(
    src: DDR5,
    dst: DDR5,
    width: DDR5Width = DDR5Width.x16,
    rank: DDR5Rank = DDR5Rank.SingleRank,
    topology: DDR5Topology = DDR5Topology.FlyBy,
    diff_ck_rs: DifferentialRoutingStructure | None = None,
    diff_dqs_rs: DifferentialRoutingStructure | None = None,
    se_dq_rs: RoutingStructure | None = None,
    se_rs: RoutingStructure | None = None,
):
    """Connect and constrain a DDR5 discrete point-to-point link.

    Convenience function that creates a DDR5Constraint and applies it via
    ``constrain_topology``.

    Args:
        src: Source DDR5 port (controller side)
        dst: Destination DDR5 port (memory side)
        width: DDR5 channel width (default: x16)
        rank: Rank configuration (default: SingleRank)
        topology: Connection topology (default: FlyBy)
        diff_ck_rs: Differential routing structure for CK (80Ω ±10%).
            If None, auto-resolved from current substrate.
        diff_dqs_rs: Differential routing structure for DQS (80Ω ±10%).
            If None, auto-resolved from current substrate.
        se_dq_rs: Single-ended routing structure for DQ/DMI (40Ω ±10%).
            If None, auto-resolved from current substrate.
        se_rs: Single-ended routing structure for CA signals (40Ω ±10%).
            If None, auto-resolved from current substrate.

    Returns:
        The DDR5Constraint that was applied.
    """
    constraint = DDR5Constraint(
        width=width,
        rank=rank,
        topology=topology,
        diff_ck_rs=diff_ck_rs,
        diff_dqs_rs=diff_dqs_rs,
        se_dq_rs=se_dq_rs,
        se_rs=se_rs,
    )
    constraint.constrain_topology(src, dst)
    return constraint
