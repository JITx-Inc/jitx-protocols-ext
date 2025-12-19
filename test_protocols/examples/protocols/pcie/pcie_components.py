"""PCIe Example Components

Translation of jsl/examples/protocols/pcie/pcie-src.stanza

This provides a dummy PCIe switch component (8x8 BGA) with multiple
PCIe port configurations (x1, x2, x4) and associated control signals.
"""

from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.component import Component
from jitx.net import Port, Provide
from jitx.si import TerminatingPinModel

from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from ....protocols.pcie import PCIe, PCIeWidth


class PCIeSwitchBGALandpattern(BGA):
    """8x8 BGA Landpattern for PCIe Switch Component

    64-ball BGA with 2mm pitch, 0.5mm ball diameter.
    Translation of BGA-pkg from pcie-src.stanza.
    """

    def __init__(self):
        super().__init__(
            num_rows=8,
            num_cols=8,
            ball_diameter=0.5,
            pitch=2.0,
        )
        self.pad_config(SMDPadConfig(copper=-0.05))


class PCIeSwitchComponent(Component):
    """Dummy PCIe Switch Component

    Translation of `component` from pcie-src.stanza.

    This is a dummy device with multiple PCIe supports demonstrating
    how to map physical pins to PCIe bundles. It has 4 lanes of TX/RX,
    4 reference clocks, 4 PERST# signals, and GPIO pins.

    Pin mapping (8x8 BGA, A-H rows, 1-8 columns):
    - REFCLK[0-3]: Reference clocks (diff pairs)
    - PTXP/PTXN[0-3]: TX differential pairs
    - PRXP/PRXN[0-3]: RX differential pairs
    - PERST#[0-3]: Reset signals
    - GPIO[1-21]: General purpose I/O for control signals
    """

    reference_prefix = "U"
    mpn = "JITX001"
    description = "Dummy device with multiple PCIe supports"

    # Reference clocks (4 differential pairs)
    REFCLKP = [Port() for _ in range(4)]
    REFCLKN = [Port() for _ in range(4)]

    # TX differential pairs (4 lanes)
    PTXP = [Port() for _ in range(4)]
    PTXN = [Port() for _ in range(4)]

    # RX differential pairs (4 lanes)
    PRXP = [Port() for _ in range(4)]
    PRXN = [Port() for _ in range(4)]

    # PERST# signals (4 reset lines)
    PERST = [Port() for _ in range(4)]

    # GPIO pins for control signals (21 pins, indexed 1-21)
    GPIO = [Port() for _ in range(21)]

    landpattern = PCIeSwitchBGALandpattern()

    # Pad mapping based on pcie-src.stanza pin-properties
    mapping = [
        PadMapping(
            {
                # Reference clocks
                REFCLKN[0]: landpattern.A[1],
                REFCLKP[0]: landpattern.A[2],
                REFCLKP[1]: landpattern.D[4],
                REFCLKN[1]: landpattern.D[3],
                REFCLKP[2]: landpattern.D[2],
                REFCLKN[2]: landpattern.D[1],
                REFCLKP[3]: landpattern.C[7],
                REFCLKN[3]: landpattern.C[6],
                # TX pairs
                PTXP[0]: landpattern.B[3],
                PTXN[0]: landpattern.B[2],
                PTXP[1]: landpattern.A[8],
                PTXN[1]: landpattern.A[7],
                PTXP[2]: landpattern.C[4],
                PTXN[2]: landpattern.C[3],
                PTXP[3]: landpattern.C[2],
                PTXN[3]: landpattern.C[1],
                # RX pairs
                PRXP[0]: landpattern.A[6],
                PRXN[0]: landpattern.A[5],
                PRXP[1]: landpattern.A[4],
                PRXN[1]: landpattern.A[3],
                PRXP[2]: landpattern.B[7],
                PRXN[2]: landpattern.B[6],
                PRXP[3]: landpattern.B[5],
                PRXN[3]: landpattern.B[4],
                # PERST# signals
                PERST[0]: landpattern.C[5],
                PERST[3]: landpattern.D[5],
                PERST[2]: landpattern.D[6],
                PERST[1]: landpattern.D[7],
                # GPIO (indexed 0-20, mapping to GPIO[1]-GPIO[21])
                GPIO[0]: landpattern.E[1],
                GPIO[1]: landpattern.E[2],
                GPIO[2]: landpattern.E[3],
                GPIO[3]: landpattern.E[4],
                GPIO[4]: landpattern.E[5],
                GPIO[5]: landpattern.E[6],
                GPIO[6]: landpattern.E[7],
                GPIO[7]: landpattern.F[1],
                GPIO[8]:  landpattern.F[2],
                GPIO[9]:  landpattern.F[3],
                GPIO[10]: landpattern.F[4],
                GPIO[11]: landpattern.F[5],
                GPIO[12]: landpattern.F[6],
                GPIO[13]: landpattern.F[7],
                GPIO[14]: landpattern.G[1],
                GPIO[15]: landpattern.G[2],
                GPIO[16]: landpattern.G[3],
                GPIO[17]: landpattern.G[4],
                GPIO[18]: landpattern.G[5],
                GPIO[19]: landpattern.G[6],
                GPIO[20]: landpattern.G[7],
            }
        )
    ]

    # Diff-pair pin models for SI constraints
    # Translation of diff-pin-model calls from pcie-src.stanza
    pin_models = []
    for i in range(4):
        pin_models.append(TerminatingPinModel((PRXP[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((PTXP[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((REFCLKP[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((PRXN[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((PTXN[i]), delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel((REFCLKN[i]), delay=10.0e-15, loss=0.1))

    for i in range(20):
        pin_models.append(TerminatingPinModel((GPIO[i]), delay=10.0e-15, loss=0.1))


    symbol = BoxSymbol()


class PCIeSwitchCircuit(Circuit):
    """PCIe Switch Circuit with Multiple PCIe Supports

    Translation of `module` from pcie-src.stanza.

    This circuit wraps the PCIeSwitchComponent and provides multiple
    PCIe port configurations through the Provide mechanism:
    - 1x PCIe x4 (with and without PRSNT#)
    - 2x PCIe x2 (with and without PRSNT#)
    - 4x PCIe x1 (with and without PRSNT#)
    """

    def __init__(self):
        self.sw = PCIeSwitchComponent()

        # Create PCIe x4 provide (without PRSNT#)
        self.pcie_x4 = Provide(PCIe(PCIeWidth.x4, on_board=False)).one_of(
            lambda b: [self._create_x4_mapping(b, 0, has_prsnt=False)]
        )

        # Create PCIe x4 provide (with PRSNT#)
        self.pcie_x4_prsnt = Provide(
            PCIe(PCIeWidth.x4, on_board=False, prsnt=True)
        ).one_of(lambda b: [self._create_x4_mapping(b, 0, has_prsnt=True)])

        # Create PCIe x2 provides (2 ports)
        self.pcie_x2 = [
            Provide(PCIe(PCIeWidth.x2, on_board=False)).one_of(
                lambda b, j=j: [self._create_x2_mapping(b, 2 * j, j, has_prsnt=False)]
            )
            for j in range(2)
        ]
        self.pcie_x2_prsnt = [
            Provide(PCIe(PCIeWidth.x2, on_board=False, prsnt=True)).one_of(
                lambda b, j=j: [self._create_x2_mapping(b, 2 * j, j, has_prsnt=True)]
            )
            for j in range(2)
        ]

        # Create PCIe x1 provides (4 ports)
        self.pcie_x1 = [
            Provide(PCIe(PCIeWidth.x1, on_board=False)).one_of(
                lambda b, j=j: [self._create_x1_mapping(b, j, has_prsnt=False)]
            )
            for j in range(4)
        ]
        self.pcie_x1_prsnt = [
            Provide(PCIe(PCIeWidth.x1, on_board=False, prsnt=True)).one_of(
                lambda b, j=j: [self._create_x1_mapping(b, j, has_prsnt=True)]
            )
            for j in range(4)
        ]

    def _create_x4_mapping(self, b: PCIe, lane_offset: int, has_prsnt: bool) -> dict:
        """Create mapping dict for x4 PCIe bundle to switch pins"""
        mapping = {}

        # Map lanes
        for i in range(4):
            mapping[b.data.lane[i].RX.p] = self.sw.PRXP[i + lane_offset]
            mapping[b.data.lane[i].RX.n] = self.sw.PRXN[i + lane_offset]
            mapping[b.data.lane[i].TX.p] = self.sw.PTXP[i + lane_offset]
            mapping[b.data.lane[i].TX.n] = self.sw.PTXN[i + lane_offset]

        # Reference clock (optional for on-board connections)
        if b.data.refclk is not None:
            mapping[b.data.refclk.p] = self.sw.REFCLKP[lane_offset]
            mapping[b.data.refclk.n] = self.sw.REFCLKN[lane_offset]

        # Control signals (optional for on-board connections)
        if b.control is not None:
            mapping[b.control.PEWAKE] = self.sw.GPIO[4]
            mapping[b.control.PERST] = self.sw.PERST[lane_offset]
            mapping[b.control.CLKREQ] = self.sw.GPIO[0]

            if b.control.PRSNT is not None:
                mapping[b.control.PRSNT] = self.sw.GPIO[11]

        return mapping

    def _create_x2_mapping(
        self, b: PCIe, lane_offset: int, port_idx: int, has_prsnt: bool
    ) -> dict:
        """Create mapping dict for x2 PCIe bundle to switch pins"""
        # Control signal mapping per port
        ctl_mapping = [
            (5, 11, 0),  # port 0
            (6, 12, 1),  # port 1
        ]
        wake_gpio, prsnt_gpio, clkreq_gpio = ctl_mapping[port_idx]

        mapping = {}

        # Map lanes
        for i in range(2):
            mapping[b.data.lane[i].RX.p] = self.sw.PRXP[i + lane_offset]
            mapping[b.data.lane[i].RX.n] = self.sw.PRXN[i + lane_offset]
            mapping[b.data.lane[i].TX.p] = self.sw.PTXP[i + lane_offset]
            mapping[b.data.lane[i].TX.n] = self.sw.PTXN[i + lane_offset]

        # Reference clock (optional for on-board connections)
        if b.data.refclk is not None:
            mapping[b.data.refclk.p] = self.sw.REFCLKP[lane_offset]
            mapping[b.data.refclk.n] = self.sw.REFCLKN[lane_offset]

        # Control signals (optional for on-board connections)
        if b.control is not None:
            mapping[b.control.PEWAKE] = self.sw.GPIO[wake_gpio]
            mapping[b.control.PERST] = self.sw.PERST[lane_offset]
            mapping[b.control.CLKREQ] = self.sw.GPIO[clkreq_gpio]

            if b.control.PRSNT is not None:
                mapping[b.control.PRSNT] = self.sw.GPIO[prsnt_gpio]

        return mapping

    def _create_x1_mapping(self, b: PCIe, lane_idx: int, has_prsnt: bool) -> dict:
        """Create mapping dict for x1 PCIe bundle to switch pins"""
        # Control signal mapping per lane
        ctl_mapping = [
            (7, 11, 0),  # lane 0
            (8, 13, 2),  # lane 1
            (9, 12, 1),  # lane 2
            (10, 14, 3),  # lane 3
        ]
        wake_gpio, prsnt_gpio, clkreq_gpio = ctl_mapping[lane_idx]

        mapping = {}

        # Map single lane
        mapping[b.data.lane[0].RX.p] = self.sw.PRXP[lane_idx]
        mapping[b.data.lane[0].RX.n] = self.sw.PRXN[lane_idx]
        mapping[b.data.lane[0].TX.p] = self.sw.PTXP[lane_idx]
        mapping[b.data.lane[0].TX.n] = self.sw.PTXN[lane_idx]

        # Reference clock (optional for on-board connections)
        if b.data.refclk is not None:
            mapping[b.data.refclk.p] = self.sw.REFCLKP[lane_idx]
            mapping[b.data.refclk.n] = self.sw.REFCLKN[lane_idx]

        # Control signals (optional for on-board connections)
        if b.control is not None:
            mapping[b.control.PEWAKE] = self.sw.GPIO[wake_gpio]
            mapping[b.control.PERST] = self.sw.PERST[lane_idx]
            mapping[b.control.CLKREQ] = self.sw.GPIO[clkreq_gpio]

            if b.control.PRSNT is not None:
                mapping[b.control.PRSNT] = self.sw.GPIO[prsnt_gpio]

        return mapping
