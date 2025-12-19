"""SATA Example Components

This provides dummy SATA controller/host components with multiple
SATA port configurations and associated control signals.
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

from ....protocols.sata import SATA


class SATASwitchBGALandpattern(BGA):
    """8x8 BGA Landpattern for SATA Switch Component

    64-ball BGA with 2mm pitch, 0.5mm ball diameter.
    """

    def __init__(self):
        super().__init__(
            num_rows=8,
            num_cols=8,
            ball_diameter=0.5,
            pitch=2.0,
        )
        self.pad_config(SMDPadConfig(copper=-0.05))


class SATASwitchComponent(Component):
    """Dummy SATA Switch/Controller Component

    This is a dummy device with multiple SATA supports demonstrating
    how to map physical pins to SATA bundles. It has 4 SATA ports
    with TX/RX differential pairs and GPIO pins for control.

    Pin mapping (8x8 BGA, A-H rows, 1-8 columns):
    - TXP/TXN[0-3]: TX differential pairs
    - RXP/RXN[0-3]: RX differential pairs
    - GPIO[0-15]: General purpose I/O for control signals
    """

    reference_prefix = "U"
    mpn = "JITX-SATA-001"
    description = "Dummy device with multiple SATA supports"

    # TX differential pairs (4 ports)
    TXP = [Port() for _ in range(4)]
    TXN = [Port() for _ in range(4)]

    # RX differential pairs (4 ports)
    RXP = [Port() for _ in range(4)]
    RXN = [Port() for _ in range(4)]

    # GPIO pins for control signals (16 pins)
    GPIO = [Port() for _ in range(16)]

    landpattern = SATASwitchBGALandpattern()

    # Pad mapping
    mapping = [
        PadMapping(
            {
                # TX pairs
                TXP[0]: landpattern.A[1],
                TXN[0]: landpattern.A[2],
                TXP[1]: landpattern.A[3],
                TXN[1]: landpattern.A[4],
                TXP[2]: landpattern.A[5],
                TXN[2]: landpattern.A[6],
                TXP[3]: landpattern.A[7],
                TXN[3]: landpattern.A[8],
                # RX pairs
                RXP[0]: landpattern.B[1],
                RXN[0]: landpattern.B[2],
                RXP[1]: landpattern.B[3],
                RXN[1]: landpattern.B[4],
                RXP[2]: landpattern.B[5],
                RXN[2]: landpattern.B[6],
                RXP[3]: landpattern.B[7],
                RXN[3]: landpattern.B[8],
                # GPIO
                GPIO[0]: landpattern.C[1],
                GPIO[1]: landpattern.C[2],
                GPIO[2]: landpattern.C[3],
                GPIO[3]: landpattern.C[4],
                GPIO[4]: landpattern.C[5],
                GPIO[5]: landpattern.C[6],
                GPIO[6]: landpattern.C[7],
                GPIO[7]: landpattern.C[8],
                GPIO[8]: landpattern.D[1],
                GPIO[9]: landpattern.D[2],
                GPIO[10]: landpattern.D[3],
                GPIO[11]: landpattern.D[4],
                GPIO[12]: landpattern.D[5],
                GPIO[13]: landpattern.D[6],
                GPIO[14]: landpattern.D[7],
                GPIO[15]: landpattern.D[8],
            }
        )
    ]

    # Diff-pair pin models for SI constraints
    pin_models = []
    for i in range(4):
        pin_models.append(TerminatingPinModel((TXP[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((TXN[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((RXP[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((RXN[i]), delay=10.0e-15, loss=0.1))

    for i in range(16):
        pin_models.append(TerminatingPinModel((GPIO[i]), delay=10.0e-15, loss=0.1))

    symbol = BoxSymbol()


class SATASwitchCircuit(Circuit):
    """SATA Switch Circuit with Multiple SATA Supports

    This circuit wraps the SATASwitchComponent and provides multiple
    SATA port configurations through the Provide mechanism:
    - 4x SATA ports (one per lane)
    """

    def __init__(self):
        self.sw = SATASwitchComponent()

        # Create SATA provides (4 ports)
        self.sata_ports = [
            Provide(SATA()).one_of(
                lambda b, j=j: [self._create_sata_mapping(b, j)]
            )
            for j in range(4)
        ]

    def _create_sata_mapping(self, b: SATA, port_idx: int) -> dict:
        """Create mapping dict for SATA bundle to switch pins"""
        mapping = {}

        # Map lane (TX and RX differential pairs)
        mapping[b.lane.TX.p] = self.sw.TXP[port_idx]
        mapping[b.lane.TX.n] = self.sw.TXN[port_idx]
        mapping[b.lane.RX.p] = self.sw.RXP[port_idx]
        mapping[b.lane.RX.n] = self.sw.RXN[port_idx]

        return mapping
