"""SFP Example Components

This provides dummy SFP/QSFP switch components with multiple
port configurations and associated control signals.
Follows the pattern from jsl/examples/protocols/pcie/pcie-src.stanza
"""

from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.component import Component
from jitx.net import Port, Provide
from jitx.si import TerminatingPinModel
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from ....protocols.sfp import QSFP, SFP, SFP_Lane


class SFPSwitchBGALandpattern(BGA):
    """12x12 BGA Landpattern for SFP Switch Component

    144-ball BGA with 1mm pitch, 0.5mm ball diameter.
    """

    def __init__(self):
        super().__init__(
            num_rows=12,
            num_cols=12,
            ball_diameter=0.5,
            pitch=1.0,
        )
        self.pad_config(SMDPadConfig(copper=-0.05))


class SFPSwitchComponent(Component):
    """Dummy SFP/QSFP Switch Component

    This is a dummy device with multiple SFP/QSFP supports demonstrating
    how to map physical pins to SFP bundles. It has 8 lanes worth of
    TX/RX differential pairs (enough for 1 QSFP-DD or 2 QSFP ports).

    Pin mapping (12x12 BGA, A-M rows, 1-12 columns):
    - TXP/TXN[0-7]: TX differential pairs (8 lanes)
    - RXP/RXN[0-7]: RX differential pairs (8 lanes)
    - GPIO[0-15]: General purpose I/O for control signals
    """

    reference_prefix = "U"
    mpn = "JITX-SFP-001"
    description = "Dummy device with multiple SFP/QSFP supports"

    # TX differential pairs (8 lanes)
    TXP = [Port() for _ in range(8)]
    TXN = [Port() for _ in range(8)]

    # RX differential pairs (8 lanes)
    RXP = [Port() for _ in range(8)]
    RXN = [Port() for _ in range(8)]

    # GPIO pins for control signals
    GPIO = [Port() for _ in range(16)]

    landpattern = SFPSwitchBGALandpattern()

    # Pad mapping
    mapping = [
        PadMapping(
            {
                # TX pairs (lanes 0-7)
                TXP[0]: landpattern.A[1],
                TXN[0]: landpattern.A[2],
                TXP[1]: landpattern.A[3],
                TXN[1]: landpattern.A[4],
                TXP[2]: landpattern.A[5],
                TXN[2]: landpattern.A[6],
                TXP[3]: landpattern.A[7],
                TXN[3]: landpattern.A[8],
                TXP[4]: landpattern.A[9],
                TXN[4]: landpattern.A[10],
                TXP[5]: landpattern.A[11],
                TXN[5]: landpattern.A[12],
                TXP[6]: landpattern.B[1],
                TXN[6]: landpattern.B[2],
                TXP[7]: landpattern.B[3],
                TXN[7]: landpattern.B[4],
                # RX pairs (lanes 0-7)
                RXP[0]: landpattern.B[5],
                RXN[0]: landpattern.B[6],
                RXP[1]: landpattern.B[7],
                RXN[1]: landpattern.B[8],
                RXP[2]: landpattern.B[9],
                RXN[2]: landpattern.B[10],
                RXP[3]: landpattern.B[11],
                RXN[3]: landpattern.B[12],
                RXP[4]: landpattern.C[1],
                RXN[4]: landpattern.C[2],
                RXP[5]: landpattern.C[3],
                RXN[5]: landpattern.C[4],
                RXP[6]: landpattern.C[5],
                RXN[6]: landpattern.C[6],
                RXP[7]: landpattern.C[7],
                RXN[7]: landpattern.C[8],
                # GPIO
                GPIO[0]: landpattern.D[1],
                GPIO[1]: landpattern.D[2],
                GPIO[2]: landpattern.D[3],
                GPIO[3]: landpattern.D[4],
                GPIO[4]: landpattern.D[5],
                GPIO[5]: landpattern.D[6],
                GPIO[6]: landpattern.D[7],
                GPIO[7]: landpattern.D[8],
                GPIO[8]: landpattern.D[9],
                GPIO[9]: landpattern.D[10],
                GPIO[10]: landpattern.D[11],
                GPIO[11]: landpattern.D[12],
                GPIO[12]: landpattern.E[1],
                GPIO[13]: landpattern.E[2],
                GPIO[14]: landpattern.E[3],
                GPIO[15]: landpattern.E[4],
            }
        )
    ]

    # Diff-pair pin models for SI constraints
    pin_models = []
    for i in range(8):
        pin_models.append(TerminatingPinModel((TXP[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((TXN[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((RXP[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((RXN[i]), delay=10.0e-15, loss=0.1))

    for i in range(16):
        pin_models.append(TerminatingPinModel((GPIO[i]), delay=10.0e-15, loss=0.1))

    symbol = BoxSymbol()


class SFPSwitchCircuit(Circuit):
    """SFP Switch Circuit with Multiple SFP/QSFP Supports

    This circuit wraps the SFPSwitchComponent and provides multiple
    SFP/QSFP port configurations through the Provide mechanism:
    - 8x SFP ports (single lane each)
    - 2x QSFP ports (4 lanes each)
    """

    def __init__(self):
        self.sw = SFPSwitchComponent()

        # Create SFP provides (8 single-lane ports)
        self.sfp_ports = [
            Provide(SFP()).one_of(
                lambda b, j=j: [self._create_sfp_mapping(b, j)]
            )
            for j in range(8)
        ]

        # Create QSFP provides (2 four-lane ports)
        self.qsfp_ports = [
            Provide(QSFP()).one_of(
                lambda b, j=j: [self._create_qsfp_mapping(b, j * 4)]
            )
            for j in range(2)
        ]

    def _create_sfp_mapping(self, b: SFP_Lane, lane_idx: int) -> dict:
        """Create mapping dict for single SFP lane to switch pins"""
        mapping = {}

        # Map single lane (TX and RX differential pairs)
        mapping[b.lanes[0].TX.p] = self.sw.TXP[lane_idx]
        mapping[b.lanes[0].TX.n] = self.sw.TXN[lane_idx]
        mapping[b.lanes[0].RX.p] = self.sw.RXP[lane_idx]
        mapping[b.lanes[0].RX.n] = self.sw.RXN[lane_idx]

        return mapping

    def _create_qsfp_mapping(self, b: SFP_Lane, lane_offset: int) -> dict:
        """Create mapping dict for QSFP (4 lanes) to switch pins"""
        mapping = {}

        # Map all 4 lanes
        for i in range(4):
            mapping[b.lanes[i].TX.p] = self.sw.TXP[lane_offset + i]
            mapping[b.lanes[i].TX.n] = self.sw.TXN[lane_offset + i]
            mapping[b.lanes[i].RX.p] = self.sw.RXP[lane_offset + i]
            mapping[b.lanes[i].RX.n] = self.sw.RXN[lane_offset + i]

        return mapping
