"""GDDR7 Memory Protocol

Graphics Double Data Rate 7 (GDDR7) is a high speed memory protocol for graphics applications.
https://en.wikipedia.org/wiki/GDDR7_SDRAM

This file supports defining GDDR7 connections between GPUs and graphics memory.

## GDDR7 Constraints

1. RCK intra-pair skew: ±10fs
2. WCK intra-pair skew: ±10fs
3. RCK to WCK skew: ±20ps
4. WCK to CA skew: ±20ps
5. RCK to DQ/DQE skew: ±20ps
6. WCK to DQ/DQE skew: ±20ps
7. DQ to DQE skew: ±5ps
8. Reset to CA skew: ±100ps
9. ERR to WCK skew: ±100ps
10. CA to CA skew: ±5ps
11. Maximum loss: 5.0dB
12. RCK/WCK differential impedance: 100Ω ±10%
13. DQ/DQE/CA/ERR single-ended impedance: 50Ω ±10%
"""

from __future__ import annotations

from dataclasses import dataclass

from jitx import current
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


class GDDR7DataChannel(Port):
    """GDDR7 Data Channel Bundle

    One of four data channels (A, B, C, or D) in a GDDR7 interface.

    Attributes:
        DQ: 10-bit data bus (PAM3 or NRZ)
        RCK: Read clock differential pair (NRZ)
        WCK: Write clock differential pair (NRZ)
        CA: 5-bit command/address bus (NRZ)
        DQE: Data bit error detection
        ERR: Error flag
    """

    DQ = [Port() for _ in range(10)]
    "10-bit data bus"

    RCK = DiffPair()
    "Read clock differential pair"

    WCK = DiffPair()
    "Write clock differential pair"

    CA = [Port() for _ in range(5)]
    "5-bit command/address bus"

    DQE = Port()
    "Data bit error detection"

    ERR = Port()
    "Error flag"


class GDDR7ControlChannel(Port):
    """GDDR7 Control Channel Bundle

    Shared control signals across all four data channels.

    Attributes:
        RESET_n: Reset signal (active low)
        ZQ_AB: Impedance calibration for channels A and B
        ZQ_CD: Impedance calibration for channels C and D
    """

    RESET_n = Port()
    "Reset signal (active low)"

    ZQ_AB = Port()
    "Impedance calibration for channels A/B"

    ZQ_CD = Port()
    "Impedance calibration for channels C/D"


class GDDR7(Port):
    """GDDR7 Memory Bundle

    Complete GDDR7 interface with 4 data channels and control.

    Attributes:
        data: 4 data channels (A, B, C, D)
        control: Shared control channel
    """

    data = [GDDR7DataChannel() for _ in range(4)]
    "4 data channels (A, B, C, D)"

    control = GDDR7ControlChannel()
    "Shared control channel"


@dataclass(frozen=True)
class GDDR7Impedances:
    """GDDR7 Impedance Specifications

    Attributes:
        diff_impedance: RCK/WCK differential impedance (default: 100Ω ±10%)
        se_impedance: DQ/DQE/CA/ERR single-ended impedance (default: 50Ω ±10%)
    """

    diff_impedance: Toleranced = Toleranced.percent(100, 10)
    "RCK/WCK differential impedance"

    se_impedance: Toleranced = Toleranced.percent(50, 10)
    "DQ/DQE/CA/ERR single-ended impedance"


@dataclass(frozen=True)
class GDDR7ConstraintParams:
    """GDDR7 Constraint Parameters"""

    skew_rck: Toleranced = Toleranced(0, 10.0e-15)
    "RCK intra-pair skew"

    skew_wck: Toleranced = Toleranced(0, 10.0e-15)
    "WCK intra-pair skew"

    skew_rck_wck: Toleranced = Toleranced(0, 20.0e-12)
    "RCK to WCK inter-pair skew"

    skew_wck_ca: Toleranced = Toleranced(0, 20.0e-12)
    "WCK to CA skew"

    skew_rck_dq: Toleranced = Toleranced(0, 20.0e-12)
    "RCK to DQ/DQE skew"

    skew_wck_dq: Toleranced = Toleranced(0, 20.0e-12)
    "WCK to DQ/DQE skew"

    skew_dq_dqe: Toleranced = Toleranced(0, 5.0e-12)
    "DQ to DQE skew"

    skew_reset_ca: Toleranced = Toleranced(0, 100.0e-12)
    "Reset to CA skew"

    skew_err_wck: Toleranced = Toleranced(0, 100.0e-12)
    "ERR to WCK skew"

    skew_ca_ca: Toleranced = Toleranced(0, 5.0e-12)
    "CA to CA skew"

    loss: float = 5.0
    "Maximum loss in dB"


class GDDR7Constraint(SignalConstraint["GDDR7"]):
    """Signal Integrity Constraint for GDDR7

    Applies comprehensive timing and routing constraints to all GDDR7 signals.

    Args:
        params: Constraint parameters
        diff_structure: Differential routing structure for RCK/WCK (100Ω)
        se_structure: Single-ended routing structure for DQ/CA (50Ω)
    """

    def __init__(
        self,
        params: GDDR7ConstraintParams | None = None,
        diff_structure: DifferentialRoutingStructure | None = None,
        se_structure: RoutingStructure | None = None,
    ):
        super().__init__()
        self.params = params or GDDR7ConstraintParams()

        if not diff_structure:
            diff_structure = current.substrate.differential_routing_structure(
                GDDR7Impedances().diff_impedance
            )
        if not se_structure:
            se_structure = current.substrate.routing_structure(GDDR7Impedances().se_impedance)

        self.rck_constraint = DiffPairConstraint(
            skew=self.params.skew_rck, loss=self.params.loss, structure=diff_structure
        )
        self.wck_constraint = DiffPairConstraint(
            skew=self.params.skew_wck, loss=self.params.loss, structure=diff_structure
        )
        self.se_structure = se_structure

    def constrain(self, src: GDDR7, dst: GDDR7):
        """Apply all GDDR7 constraints

        Args:
            src: Source GDDR7 port
            dst: Destination GDDR7 port
        """
        # Constrain each of the 4 data channels
        for _ch_idx, (src_ch, dst_ch) in enumerate(zip(src.data, dst.data, strict=True)):
            # RCK and WCK constraints
            self.rck_constraint.constrain(src_ch.RCK, dst_ch.RCK)
            self.wck_constraint.constrain(src_ch.WCK, dst_ch.WCK)

            guide_rck = Topology(src_ch.RCK.p, dst_ch.RCK.p)
            guide_wck = Topology(src_ch.WCK.p, dst_ch.WCK.p)

            # RCK to WCK timing
            self.add(
                ConstrainReferenceDifference(guide_rck, [guide_wck]).timing_difference(
                    self.params.skew_rck_wck
                )
            )

            # CA signals
            ca_topos = [
                Topology(src_ca, dst_ca)
                for src_ca, dst_ca in zip(src_ch.CA, dst_ch.CA, strict=True)
            ]

            # WCK to CA timing
            for ca_topo in ca_topos:
                self.add(
                    ConstrainReferenceDifference(guide_wck, [ca_topo]).timing_difference(
                        self.params.skew_wck_ca
                    )
                )
                ca_constrained = Constrain(ca_topo).insertion_loss(self.params.loss)
                ca_constrained.structure(self.se_structure)
                self.add(ca_constrained)

            # CA to CA timing (use CA[0] as reference)
            if ca_topos:
                for ca_topo in ca_topos[1:]:
                    self.add(
                        ConstrainReferenceDifference(ca_topos[0], [ca_topo]).timing_difference(
                            self.params.skew_ca_ca
                        )
                    )

            # DQ and DQE signals
            for src_dq, dst_dq in zip(src_ch.DQ, dst_ch.DQ, strict=True):
                dq_topo = Topology(src_dq, dst_dq)
                # RCK to DQ and WCK to DQ timing
                self.add(
                    ConstrainReferenceDifference(guide_rck, [dq_topo]).timing_difference(
                        self.params.skew_rck_dq
                    )
                )
                self.add(
                    ConstrainReferenceDifference(guide_wck, [dq_topo]).timing_difference(
                        self.params.skew_wck_dq
                    )
                )
                dq_constrained = Constrain(dq_topo).insertion_loss(self.params.loss)
                dq_constrained.structure(self.se_structure)
                self.add(dq_constrained)

            # DQE signal
            dqe_topo = Topology(src_ch.DQE, dst_ch.DQE)
            self.add(
                ConstrainReferenceDifference(guide_rck, [dqe_topo]).timing_difference(
                    self.params.skew_rck_dq
                )
            )
            dqe_constrained = Constrain(dqe_topo).insertion_loss(self.params.loss)
            dqe_constrained.structure(self.se_structure)
            self.add(dqe_constrained)

            # ERR signal
            err_topo = Topology(src_ch.ERR, dst_ch.ERR)
            self.add(
                ConstrainReferenceDifference(guide_wck, [err_topo]).timing_difference(
                    self.params.skew_err_wck
                )
            )
            err_constrained = Constrain(err_topo).insertion_loss(self.params.loss)
            err_constrained.structure(self.se_structure)
            self.add(err_constrained)

        # Control channel signals
        reset_topo = Topology(src.control.RESET_n, dst.control.RESET_n)
        reset_constrained = Constrain(reset_topo).insertion_loss(self.params.loss)
        reset_constrained.structure(self.se_structure)
        self.add(reset_constrained)

        # Reset to CA timing (use first channel's first CA as reference)
        if src.data and src.data[0].CA:
            first_ca = Topology(src.data[0].CA[0], dst.data[0].CA[0])
            self.add(
                ConstrainReferenceDifference(reset_topo, [first_ca]).timing_difference(
                    self.params.skew_reset_ca
                )
            )


def connect_gddr7(
    src: GDDR7,
    dst: GDDR7,
    diff_structure: DifferentialRoutingStructure | None = None,
    se_structure: RoutingStructure | None = None,
):
    """Connect and constrain a GDDR7 link.

    Convenience function that creates a GDDR7Constraint and applies it via
    ``constrain_topology``. Equivalent to Stanza's ``connect-GDDR7``.

    Args:
        src: Source GDDR7 port (GPU side)
        dst: Destination GDDR7 port (memory side)
        diff_structure: Differential routing structure for RCK/WCK (100Ω ±10%).
            If None, auto-resolved from current substrate.
        se_structure: Single-ended routing structure for DQ/CA (50Ω ±10%).
            If None, auto-resolved from current substrate.

    Returns:
        The GDDR7Constraint that was applied.
    """
    constraint = GDDR7Constraint(
        diff_structure=diff_structure,
        se_structure=se_structure,
    )
    constraint.constrain_topology(src, dst)
    return constraint
