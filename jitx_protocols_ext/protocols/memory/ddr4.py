"""DDR4 Memory Protocol

DDR4 is a high speed memory protocol.
https://en.wikipedia.org/wiki/DDR4_SDRAM

The functions and definitions in this file support defining DDR4 connections between
microprocessors and memories in a board design. The DDR4 standard is a complex
specification with many timing constraints and impedance requirements.

This implementation is based on the DDR4 SDRAM Standard Version 4.00, October 2018.
This file supports both point-to-point and FlyBy connections.

## DDR4 Timing Constraints

The DDR4 specification defines multiple timing relationships:

1. Skew match between A[17] A[13:0] and CK.P is 0.0 +/- 20e-12 (20 ps)
2. Skew match between RAS_n, CAS_n, WE_n, and CK.P is 0.0 +/- 20e-12 (20 ps)
3. Skew match between BA[1:0], BG[1:0] and CK.P is 0.0 +/- 20e-12 (20 ps)
4. Skew match between ACT_n, CKE, CS_n, ODT, PAR and CK.P is 0.0 +/- 20e-12 (20 ps)
5. Skew match between CMD/ADDR/CTRL within a channel is 0.0 +/- 20e-12 (20 ps)
6. Skew match of CK is 0.0 +/- 1.0e-12 (1 ps)
7. Skew match of DQS is 0.0 +/- 1.0e-12 (1 ps)
8. Skew match between DQ and DQS.P within a byte lane is 0.0 +/- 3.5e-12 (3.5 ps)
9. Skew match between CK.P and DQS.P is -85 ps to 935 ps

## References

- Intel specs: https://www.intel.com/content/www/us/en/docs/programmable/683216/23-2-2-7-1/skew-matching-guidelines-for-ddr4-discrete.html
- AMD specs: https://docs.amd.com/r/en-US/ug863-versal-pcb-design/Timing-Constraint-Rules-for-DDR4-Signals
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


class DDR4Width(Enum):
    """DDR4 Channel Width

    Possible lane widths for DDR4 memory channels (number of DQ signals).
    """

    x4 = 4
    "4 bit width"
    x8 = 8
    "8 bit width"
    x16 = 16
    "16 bit width"
    x24 = 24
    "24 bit width"
    x32 = 32
    "32 bit width"
    x36 = 36
    "36 bit width (with ECC nibble)"
    x40 = 40
    "40 bit width"
    x64 = 64
    "64 bit width"
    x72 = 72
    "72 bit width (with ECC)"


def width_to_int(width: DDR4Width) -> int:
    """Convert DDR4 width enum to integer bit width

    Args:
        width: DDR4 width enum

    Returns:
        Number of DQ bits
    """
    return width.value


def width_to_lane_count(width: DDR4Width) -> int:
    """Convert DDR4 width to number of byte lanes (DQS pairs)

    Each byte lane is 8 bits and has one DQS pair.

    Args:
        width: DDR4 width enum

    Returns:
        Number of 8-bit byte lanes (DQS pairs)
    """
    if width == DDR4Width.x4:
        return 1  # Degenerate case
    if width == DDR4Width.x8:
        return 1
    if width == DDR4Width.x16:
        return 2
    if width == DDR4Width.x24:
        return 3
    if width == DDR4Width.x32:
        return 4
    if width == DDR4Width.x36:
        return 5  # 4 data + 1 ECC nibble
    if width == DDR4Width.x40:
        return 5
    if width == DDR4Width.x64:
        return 8
    if width == DDR4Width.x72:
        return 9  # 8 data + 1 ECC
    raise ValueError(f"Unknown DDR4 width: {width}")


def rank_to_int(rank: DDR4Rank) -> int:
    """Convert DDR4 rank enum to integer count of CS_n signals.

    Args:
        rank: DDR4 rank enum

    Returns:
        Number of CS_n (and CKE, ODT) signals
    """
    return rank.value


class DDR4Topology(Enum):
    """DDR4 Topology Type

    Possible topologies for DDR4 memory connections.
    """

    FlyBy = "FlyBy"
    "FlyBy topology (daisy-chain)"


class DDR4Rank(Enum):
    """DDR4 Rank Configuration

    Number of chip select (CS_n) signals.
    """

    SingleRank = 1
    "Single rank - 1 CS_n signal"
    DualRank = 2
    "Dual rank - 2 CS_n signals"
    QuadRank = 4
    "Quad rank - 4 CS_n signals"


class DDR4DataChannel(Port):
    """DDR4 Data Channel Bundle

    Data signals for DDR4 memory.

    Args:
        width: DDR4 channel width

    Attributes:
        DQ: Data bus (width varies: 4 to 72 bits)
        DQS: Data strobe pairs (1 per 8-bit byte lane)
        DM_n: Data mask signals (1 per byte lane)
    """

    DQ: Sequence[Port]
    "Data signals"

    DQS: Sequence[DiffPair]
    "Data strobe differential pairs"

    DM_n: Sequence[Port]
    "Data mask signals (active low)"

    def __init__(self, width: DDR4Width):
        dq_count = width_to_int(width)
        lane_count = width_to_lane_count(width)

        self.DQ = tuple(Port() for _ in range(dq_count))
        self.DQS = tuple(DiffPair() for _ in range(lane_count))
        self.DM_n = tuple(Port() for _ in range(lane_count))


class DDR4AccChannel(Port):
    """DDR4 Address/Command/Control Channel Bundle

    Command, address, and control signals for DDR4 memory.

    Args:
        rank: Rank configuration (determines CS_n, CKE, ODT counts)
        ck_count: Number of CK differential pairs (default 2)
        bg_count: Number of bank group select signals (default 2)
        ba_count: Number of bank address signals (default 2)

    Attributes:
        CK: Clock differential pairs
        CKE: Clock enable signals
        A: Address bus (17 bits: A[16:0])
        ACT_n: Activate command (active low)
        BG: Bank group select
        BA: Bank address
        CS_n: Chip select (active low)
        RESET_n: Reset (active low)
        ODT: On-die termination
        PAR: Parity
        ALERT_n: Alert (active low)
    """

    CK: Sequence[DiffPair]
    "Clock differential pairs"

    CKE: Sequence[Port]
    "Clock enable signals"

    A: Sequence[Port]
    "Address bus A[16:0]"

    ACT_n = Port()
    "Activate command (active low)"

    BG: Sequence[Port]
    "Bank group select"

    BA: Sequence[Port]
    "Bank address"

    CS_n: Sequence[Port]
    "Chip select (active low)"

    RESET_n = Port()
    "Reset (active low)"

    ODT: Sequence[Port]
    "On-die termination"

    PAR = Port()
    "Parity"

    ALERT_n = Port()
    "Alert (active low)"

    def __init__(
        self, rank: DDR4Rank, ck_count: int = 2, bg_count: int = 2, ba_count: int = 2
    ):
        rank_count = rank.value

        self.CK = tuple(DiffPair() for _ in range(ck_count))
        self.CKE = tuple(Port() for _ in range(rank_count))
        self.A = tuple(Port() for _ in range(17))
        self.BG = tuple(Port() for _ in range(bg_count))
        self.BA = tuple(Port() for _ in range(ba_count))
        self.CS_n = tuple(Port() for _ in range(rank_count))
        self.ODT = tuple(Port() for _ in range(rank_count))


class DDR4(Port):
    """DDR4 Memory Bundle

    Complete DDR4 interface combining data and address/command/control channels.

    Args:
        width: Channel width (x4, x8, x16, etc.)
        rank: Rank configuration (SingleRank, DualRank, QuadRank)
        topology: Connection topology (FlyBy)
        ck_count: Number of CK differential pairs (default 2)
        bg_count: Number of bank group signals (default 2)
        ba_count: Number of bank address signals (default 2)

    Attributes:
        data: Data channel (DQ, DQS, DM_n)
        acc: Address/Command/Control channel
    """

    data: DDR4DataChannel
    "Data channel"

    acc: DDR4AccChannel
    "Address/Command/Control channel"

    def __init__(
        self,
        width: DDR4Width,
        rank: DDR4Rank = DDR4Rank.SingleRank,
        topology: DDR4Topology = DDR4Topology.FlyBy,
        ck_count: int = 2,
        bg_count: int = 2,
        ba_count: int = 2,
    ):
        # Validate configurations
        if width == DDR4Width.x4 and rank != DDR4Rank.SingleRank:
            raise ValueError("DDR4 x4 width is only supported in SingleRank configuration")
        if width == DDR4Width.x16 and rank == DDR4Rank.QuadRank:
            raise ValueError("DDR4 x16 width is not supported in QuadRank configuration")

        self.data = DDR4DataChannel(width)
        self.acc = DDR4AccChannel(rank, ck_count, bg_count, ba_count)


@dataclass(frozen=True)
class DDR4Impedances:
    """DDR4 Impedance Specifications

    Differential and single-ended impedance targets for different signal groups.

    Attributes:
        ck_impedance: CK clock impedance (default: 90Ω ±5%)
        dqs_impedance: DQS strobe impedance (default: 100Ω ±5%)
        dq_impedance: DQ data impedance (default: 50Ω ±5%)
        acc_impedance: Address/Command/Control impedance (default: 45Ω ±5%)
    """

    ck_impedance: Toleranced = Toleranced.percent(90, 5)
    "CK clock differential impedance"

    dqs_impedance: Toleranced = Toleranced.percent(100, 5)
    "DQS strobe differential impedance"

    dq_impedance: Toleranced = Toleranced.percent(50, 5)
    "DQ data single-ended impedance"

    acc_impedance: Toleranced = Toleranced.percent(45, 5)
    "Address/Command/Control single-ended impedance"


@dataclass(frozen=True)
class DDR4DataConstraintParams:
    """DDR4 Data Channel Constraint Parameters

    Timing and impedance constraints for the data channel.

    Attributes:
        skew_dqs: DQS intra-pair skew (default: ±1.0ps)
        skew_dq_dqs: DQ to DQS inter-signal skew (default: ±3.5ps)
        skew_dm_dqs: DM_n to DQS timing skew (default: ±3.5ps)
        loss: Maximum loss in dB (default: 5.0dB)
    """

    skew_dqs: Toleranced = Toleranced(0, 1.0e-12)
    "DQS intra-pair skew"

    skew_dq_dqs: Toleranced = Toleranced(0, 3.5e-12)
    "DQ to DQS inter-signal skew"

    skew_dm_dqs: Toleranced = Toleranced(0, 3.5e-12)
    "DM_n to DQS timing skew"

    loss: float = 5.0
    "Maximum loss in dB"


@dataclass(frozen=True)
class DDR4AccConstraintParams:
    """DDR4 Address/Command/Control Constraint Parameters

    Timing constraints for the ACC channel.

    Attributes:
        skew_ck: CK intra-pair skew (default: ±1.0ps)
        skew_cmd_addr_ctrl_ck: CMD/ADDR/CTRL to CK skew (default: ±20ps)
        skew_cmd_addr_ctrl: CMD/ADDR/CTRL intra-group skew (default: ±10ps)
        loss: Maximum loss in dB (default: 5.0dB)
    """

    skew_ck: Toleranced = Toleranced(0, 1.0e-12)
    "CK intra-pair skew"

    skew_cmd_addr_ctrl_ck: Toleranced = Toleranced(0, 20.0e-12)
    "CMD/ADDR/CTRL to CK inter-signal skew"

    skew_cmd_addr_ctrl: Toleranced = Toleranced(0, 10.0e-12)
    "CMD/ADDR/CTRL intra-group skew"

    loss: float = 5.0
    "Maximum loss in dB"


@dataclass(frozen=True)
class DDR4DataAccConstraintParams:
    """DDR4 Data-to-ACC Cross-Channel Constraint Parameters

    Timing relationship between data and address/command/control channels.

    Attributes:
        skew_ck_dqs: CK.P to DQS.P inter-signal skew (default: -85ps to +935ps)
    """

    skew_ck_dqs: Toleranced = Toleranced.min_typ_max(-85.0e-12, 0.0, 935.0e-12)
    "CK.P to DQS.P inter-signal timing skew"


@inner
class DDR4DataConstraint(SignalConstraint["DDR4DataChannel"]):
    """Signal Integrity Constraint for DDR4 Data Channel

    Applies constraints to DQ, DQS, and DM_n signals.

    Args:
        params: Data channel constraint parameters
        diff_dqs_structure: Differential routing structure for DQS (100Ω)
        se_dq_structure: Single-ended routing structure for DQ and DM_n (50Ω)
    """

    def __init__(
        self,
        params: DDR4DataConstraintParams | None = None,
        diff_dqs_structure: DifferentialRoutingStructure | None = None,
        se_dq_structure: RoutingStructure | None = None,
    ):
        super().__init__()
        self.params = params or DDR4DataConstraintParams()

        if not diff_dqs_structure:
            diff_dqs_structure = current.substrate.differential_routing_structure(
                DDR4Impedances().dqs_impedance
            )
        if not se_dq_structure:
            se_dq_structure = current.substrate.routing_structure(
                DDR4Impedances().dq_impedance
            )

        self.dqs_constraint = DiffPairConstraint(
            skew=self.params.skew_dqs, loss=self.params.loss, structure=diff_dqs_structure
        )
        self.se_dq_structure = se_dq_structure

    def constrain(self, src: DDR4DataChannel, dst: DDR4DataChannel):
        """Apply constraints to DDR4 data channel

        Applies per-byte-lane constraints:
        - DQS differential pair skew and loss
        - DQ to DQS timing alignment within each byte lane
        - DM_n to DQS timing alignment
        - Single-ended routing structure for DQ and DM_n

        Args:
            src: Source data channel
            dst: Destination data channel
        """
        dq_count = len(src.DQ)

        # Constrain each byte lane independently
        for i, (src_dqs, dst_dqs) in enumerate(zip(src.DQS, dst.DQS, strict=True)):
            # Constrain DQS differential pair
            self.dqs_constraint.constrain(src_dqs, dst_dqs)

            # Create reference topology from DQS.P for this byte lane
            guide_dqs = Topology(src_dqs.p, dst_dqs.p)

            # Determine DQ signals for this byte lane (8 bits per lane)
            byte_start = i * 8
            byte_end = min(byte_start + 8, dq_count)

            # Create topologies for DQ signals in this byte lane
            dq_topos = [
                Topology(src.DQ[j], dst.DQ[j]) for j in range(byte_start, byte_end)
            ]

            # Add DM_n topology for this byte lane
            dm_topo = Topology(src.DM_n[i], dst.DM_n[i])
            all_data_topos = dq_topos + [dm_topo]

            # Apply DQ/DM_n to DQS timing constraint
            self.add(
                ConstrainReferenceDifference(guide_dqs, all_data_topos).timing_difference(
                    self.params.skew_dq_dqs
                )
            )

            # Apply single-ended routing structure and loss to DQ signals
            for dq_topo in dq_topos:
                constrained = Constrain(dq_topo).insertion_loss(self.params.loss)
                constrained.structure(self.se_dq_structure)
                self.add(constrained)

            # Apply structure and loss to DM_n
            dm_constrained = Constrain(dm_topo).insertion_loss(self.params.loss)
            dm_constrained.structure(self.se_dq_structure)
            self.add(dm_constrained)


@inner
class DDR4AccConstraint(SignalConstraint["DDR4AccChannel"]):
    """Signal Integrity Constraint for DDR4 Address/Command/Control Channel

    Applies constraints to CK, address, command, and control signals.

    Args:
        params: ACC channel constraint parameters
        diff_ck_structure: Differential routing structure for CK (90Ω)
        se_structure: Single-ended routing structure for other signals (45Ω)
    """

    def __init__(
        self,
        params: DDR4AccConstraintParams | None = None,
        diff_ck_structure: DifferentialRoutingStructure | None = None,
        se_structure: RoutingStructure | None = None,
    ):
        super().__init__()
        self.params = params or DDR4AccConstraintParams()

        if not diff_ck_structure:
            diff_ck_structure = current.substrate.differential_routing_structure(
                DDR4Impedances().ck_impedance
            )
        if not se_structure:
            se_structure = current.substrate.routing_structure(
                DDR4Impedances().acc_impedance
            )

        self.ck_constraint = DiffPairConstraint(
            skew=self.params.skew_ck, loss=self.params.loss, structure=diff_ck_structure
        )
        self.se_structure = se_structure

    def constrain(self, src: DDR4AccChannel, dst: DDR4AccChannel):
        """Apply constraints to DDR4 ACC channel

        Applies constraints to:
        - CK differential pairs (intra-pair skew, inter-CK skew)
        - All CMD/ADDR/CTRL signals relative to CK
        - CMD/ADDR/CTRL signals relative to each other
        - Single-ended routing structure and loss

        Args:
            src: Source ACC channel
            dst: Destination ACC channel
        """
        # Constrain CK pairs and establish reference
        guide_cks = Topology(src.CK[0].p, dst.CK[0].p)

        for i, (src_ck, dst_ck) in enumerate(zip(src.CK, dst.CK, strict=True)):
            # Constrain each CK pair
            self.ck_constraint.constrain(src_ck, dst_ck)

            # Inter-CK skew (CK[1+] relative to CK[0])
            if i > 0:
                ck_topo = Topology(src_ck.p, dst_ck.p)
                self.add(
                    ConstrainReferenceDifference(guide_cks, [ck_topo]).timing_difference(
                        self.params.skew_ck
                    )
                )

        # Use CKE[0] as the reference for CMD/ADDR/CTRL intra-group timing
        guide_acc_group = Topology(src.CKE[0], dst.CKE[0])

        # Helper function to apply ACC signal constraints
        def constrain_acc_signal(src_sig: Port, dst_sig: Port):
            sig_topo = Topology(src_sig, dst_sig)
            # Timing relative to CK
            self.add(
                ConstrainReferenceDifference(guide_cks, [sig_topo]).timing_difference(
                    self.params.skew_cmd_addr_ctrl_ck
                )
            )
            # Timing relative to ACC group
            self.add(
                ConstrainReferenceDifference(
                    guide_acc_group, [sig_topo]
                ).timing_difference(self.params.skew_cmd_addr_ctrl)
            )
            # Structure and loss
            constrained = Constrain(sig_topo).insertion_loss(self.params.loss)
            constrained.structure(self.se_structure)
            self.add(constrained)

        # Apply constraints to all ACC signals
        for src_cke, dst_cke in zip(src.CKE, dst.CKE, strict=True):
            sig_topo = Topology(src_cke, dst_cke)
            # CKE relative to CK only (it defines the ACC group reference)
            self.add(
                ConstrainReferenceDifference(guide_cks, [sig_topo]).timing_difference(
                    self.params.skew_cmd_addr_ctrl_ck
                )
            )
            constrained = Constrain(sig_topo).insertion_loss(self.params.loss)
            constrained.structure(self.se_structure)
            self.add(constrained)

        # Address bus
        for src_a, dst_a in zip(src.A, dst.A, strict=True):
            constrain_acc_signal(src_a, dst_a)

        # Control signals
        constrain_acc_signal(src.ACT_n, dst.ACT_n)

        for src_bg, dst_bg in zip(src.BG, dst.BG, strict=True):
            constrain_acc_signal(src_bg, dst_bg)

        for src_ba, dst_ba in zip(src.BA, dst.BA, strict=True):
            constrain_acc_signal(src_ba, dst_ba)

        for src_cs, dst_cs in zip(src.CS_n, dst.CS_n, strict=True):
            constrain_acc_signal(src_cs, dst_cs)

        constrain_acc_signal(src.RESET_n, dst.RESET_n)

        for src_odt, dst_odt in zip(src.ODT, dst.ODT, strict=True):
            constrain_acc_signal(src_odt, dst_odt)

        constrain_acc_signal(src.PAR, dst.PAR)
        constrain_acc_signal(src.ALERT_n, dst.ALERT_n)


@inner
class DDR4DataAccConstraint(SignalConstraint["DDR4"]):
    """Signal Integrity Constraint for DDR4 Data-to-ACC Cross-Channel Timing

    Constrains the timing relationship between CK and DQS signals across
    the data and address/command/control channels.

    Args:
        params: Data-to-ACC constraint parameters
    """

    def __init__(self, params: DDR4DataAccConstraintParams | None = None):
        super().__init__()
        self.params = params or DDR4DataAccConstraintParams()

    def constrain(self, src: DDR4, dst: DDR4):
        """Apply cross-channel CK-to-DQS timing constraints.

        Constrains each DQS.P signal relative to CK[0].P with the
        specified timing window (default: -85ps to +935ps).

        Args:
            src: Source DDR4 port
            dst: Destination DDR4 port
        """
        guide_ck = Topology(src.acc.CK[0].p, dst.acc.CK[0].p)

        for src_dqs, dst_dqs in zip(src.data.DQS, dst.data.DQS, strict=True):
            target_dqs = Topology(src_dqs.p, dst_dqs.p)
            self.add(
                ConstrainReferenceDifference(guide_ck, [target_dqs]).timing_difference(
                    self.params.skew_ck_dqs
                )
            )


@inner
class DDR4Constraint(SignalConstraint["DDR4"]):
    """Complete DDR4 Signal Integrity Constraint

    Combines data channel, ACC channel, and cross-channel constraints.

    When explicit routing structures are provided, they are passed through to
    the sub-constraints. When omitted, the sub-constraints will auto-resolve
    routing structures from ``current.substrate``.

    Args:
        width: DDR4 channel width
        rank: Rank configuration
        topology: Memory topology (default: FlyBy)
        diff_ck_rs: Differential routing structure for CK (90Ω ±5%)
        diff_dqs_rs: Differential routing structure for DQS (100Ω ±5%)
        se_dq_rs: Single-ended routing structure for DQ/DM_n (50Ω ±5%)
        se_rs: Single-ended routing structure for ACC signals (45Ω ±5%)
        data_constraint: Data channel constraint (overrides diff_dqs_rs/se_dq_rs)
        acc_constraint: ACC channel constraint (overrides diff_ck_rs/se_rs)
        data_acc_constraint: Data-to-ACC cross-channel constraint
    """

    def __init__(
        self,
        width: DDR4Width,
        rank: DDR4Rank,
        topology: DDR4Topology = DDR4Topology.FlyBy,
        diff_ck_rs: DifferentialRoutingStructure | None = None,
        diff_dqs_rs: DifferentialRoutingStructure | None = None,
        se_dq_rs: RoutingStructure | None = None,
        se_rs: RoutingStructure | None = None,
        data_constraint: SignalConstraint[DDR4DataChannel] | None = None,
        acc_constraint: SignalConstraint[DDR4AccChannel] | None = None,
        data_acc_constraint: SignalConstraint[DDR4] | None = None,
    ):
        super().__init__()
        self.width = width
        self.rank = rank
        self.topology = topology

        if data_constraint is not None:
            self.data_constraint = data_constraint
        else:
            self.data_constraint = DDR4DataConstraint(
                diff_dqs_structure=diff_dqs_rs,
                se_dq_structure=se_dq_rs,
            )

        if acc_constraint is not None:
            self.acc_constraint = acc_constraint
        else:
            self.acc_constraint = DDR4AccConstraint(
                diff_ck_structure=diff_ck_rs,
                se_structure=se_rs,
            )

        self.data_acc_constraint: SignalConstraint[DDR4] = (
            data_acc_constraint
            if data_acc_constraint is not None
            else DDR4DataAccConstraint()
        )

    def constrain(self, src: DDR4, dst: DDR4):
        """Apply all DDR4 constraints.

        Applies:
        - Data channel constraints (DQ, DQS, DM_n)
        - ACC channel constraints (CK, address, command, control)
        - Cross-channel CK-to-DQS timing relationship

        Args:
            src: Source DDR4 port
            dst: Destination DDR4 port
        """
        self.data_constraint.constrain(src.data, dst.data)
        self.acc_constraint.constrain(src.acc, dst.acc)
        self.data_acc_constraint.constrain(src, dst)


def connect_ddr4(
    src: DDR4,
    dst: DDR4,
    width: DDR4Width = DDR4Width.x16,
    rank: DDR4Rank = DDR4Rank.SingleRank,
    topology: DDR4Topology = DDR4Topology.FlyBy,
    diff_ck_rs: DifferentialRoutingStructure | None = None,
    diff_dqs_rs: DifferentialRoutingStructure | None = None,
    se_dq_rs: RoutingStructure | None = None,
    se_rs: RoutingStructure | None = None,
):
    """Connect and constrain a DDR4 discrete point-to-point link.

    Convenience function that creates a DDR4Constraint and applies it via
    ``constrain_topology``. Equivalent to Stanza's ``connect-DDR4``.

    Args:
        src: Source DDR4 port (controller side)
        dst: Destination DDR4 port (memory side)
        width: DDR4 channel width (default: x16)
        rank: Rank configuration (default: SingleRank)
        topology: Connection topology (default: FlyBy)
        diff_ck_rs: Differential routing structure for CK (90Ω ±5%).
            If None, auto-resolved from current substrate.
        diff_dqs_rs: Differential routing structure for DQS (100Ω ±5%).
            If None, auto-resolved from current substrate.
        se_dq_rs: Single-ended routing structure for DQ/DM_n (50Ω ±5%).
            If None, auto-resolved from current substrate.
        se_rs: Single-ended routing structure for ACC signals (45Ω ±5%).
            If None, auto-resolved from current substrate.

    Returns:
        The DDR4Constraint that was applied.
    """
    constraint = DDR4Constraint(
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
