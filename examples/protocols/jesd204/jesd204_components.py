"""JESD204 Example Components

Dummy ADC and FPGA components demonstrating JESD204B/C pin mapping
with the Provide mechanism for flexible port assignment.
"""

from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.component import Component
from jitx.net import Port, Provide
from jitx.si import TerminatingPinModel
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from jitx_protocols_ext.protocols.jesd204 import JESD204, JESD204LaneCount


class JESD204BGALandpattern(BGA):
    """8x8 BGA Landpattern for JESD204 Example Components

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


class JESD204ADCComponent(Component):
    """Dummy JESD204 ADC Component (Transmitter)

    A dummy quad-channel ADC with 4 JESD204 serial output lanes,
    SYNC~ input, SYSREF input, and DEVCLK input.

    In JESD204, the ADC is the transmitter: data flows from ADC serial
    outputs (SERDOUT) to the logic device (FPGA) serial inputs.

    Pin mapping (8x8 BGA):
    - SERDOUTP/N[0-3]: Serial data output differential pairs (CML)
    - SYNCP/N: Sync input differential pair (LVDS, from FPGA)
    - SYSREFP/N: System reference input differential pair (LVDS)
    - DEVCLKP/N: Device clock input differential pair
    """

    reference_prefix = "U"
    mpn = "JITX-JESD204-ADC-001"
    description = "Dummy JESD204 ADC with 4 serial output lanes"

    # Serial data output lanes (4 differential pairs)
    SERDOUTP = [Port() for _ in range(4)]
    SERDOUTN = [Port() for _ in range(4)]

    # SYNC~ input (from receiver/FPGA)
    SYNCP = Port()
    SYNCN = Port()

    # SYSREF input
    SYSREFP = Port()
    SYSREFN = Port()

    # Device clock input
    DEVCLKP = Port()
    DEVCLKN = Port()

    landpattern = JESD204BGALandpattern()

    mapping = [
        PadMapping(
            {
                # Serial data output lanes
                SERDOUTP[0]: landpattern.A[1],
                SERDOUTN[0]: landpattern.A[2],
                SERDOUTP[1]: landpattern.A[3],
                SERDOUTN[1]: landpattern.A[4],
                SERDOUTP[2]: landpattern.A[5],
                SERDOUTN[2]: landpattern.A[6],
                SERDOUTP[3]: landpattern.A[7],
                SERDOUTN[3]: landpattern.A[8],
                # SYNC~
                SYNCP: landpattern.B[1],
                SYNCN: landpattern.B[2],
                # SYSREF
                SYSREFP: landpattern.B[3],
                SYSREFN: landpattern.B[4],
                # DEVCLK
                DEVCLKP: landpattern.B[5],
                DEVCLKN: landpattern.B[6],
            }
        )
    ]

    pin_models = []
    for i in range(4):
        pin_models.append(TerminatingPinModel(SERDOUTP[i], delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel(SERDOUTN[i], delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(SYNCP, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(SYNCN, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(SYSREFP, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(SYSREFN, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(DEVCLKP, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(DEVCLKN, delay=10.0e-15, loss=0.1))

    symbol = BoxSymbol()


class JESD204ADCCircuit(Circuit):
    """JESD204 ADC Circuit with Provide for Port Assignment

    Wraps the ADC component and provides a 4-lane JESD204 port
    through the Provide mechanism.
    """

    def __init__(self):
        self.adc = JESD204ADCComponent()

        self.jesd_port = Provide(
            JESD204(JESD204LaneCount.x4)
        ).one_of(lambda b: [self._create_mapping(b)])

    def _create_mapping(self, b: JESD204) -> dict:
        mapping = {}

        # Map data lanes (ADC SERDOUT → bundle lane)
        for i in range(len(b.lane)):
            mapping[b.lane[i].p] = self.adc.SERDOUTP[i]
            mapping[b.lane[i].n] = self.adc.SERDOUTN[i]

        # Map SYNC~ (bundle SYNC ← ADC SYNC input)
        if b.SYNC is not None:
            mapping[b.SYNC.p] = self.adc.SYNCP
            mapping[b.SYNC.n] = self.adc.SYNCN

        # Map SYSREF
        if b.SYSREF is not None:
            mapping[b.SYSREF.p] = self.adc.SYSREFP
            mapping[b.SYSREF.n] = self.adc.SYSREFN

        # Map DEVCLK
        if b.DEVCLK is not None:
            mapping[b.DEVCLK.p] = self.adc.DEVCLKP
            mapping[b.DEVCLK.n] = self.adc.DEVCLKN

        return mapping


class JESD204FPGAComponent(Component):
    """Dummy JESD204 FPGA Component (Receiver)

    A dummy FPGA with 4 JESD204 serial input lanes, SYNC~ output,
    SYSREF input, and DEVCLK input.

    In JESD204, the FPGA is the receiver: data flows from ADC serial
    outputs to the FPGA serial inputs (SERDIN). The FPGA drives SYNC~
    back to the ADC to initiate lane alignment.

    Pin mapping (8x8 BGA):
    - SERDINP/N[0-3]: Serial data input differential pairs (CML)
    - SYNCP/N: Sync output differential pair (LVDS, to ADC)
    - SYSREFP/N: System reference input differential pair (LVDS)
    - DEVCLKP/N: Device clock input differential pair
    """

    reference_prefix = "U"
    mpn = "JITX-JESD204-FPGA-001"
    description = "Dummy JESD204 FPGA with 4 serial input lanes"

    # Serial data input lanes (4 differential pairs)
    SERDINP = [Port() for _ in range(4)]
    SERDINN = [Port() for _ in range(4)]

    # SYNC~ output (to converter/ADC)
    SYNCP = Port()
    SYNCN = Port()

    # SYSREF input
    SYSREFP = Port()
    SYSREFN = Port()

    # Device clock input
    DEVCLKP = Port()
    DEVCLKN = Port()

    landpattern = JESD204BGALandpattern()

    mapping = [
        PadMapping(
            {
                # Serial data input lanes
                SERDINP[0]: landpattern.A[1],
                SERDINN[0]: landpattern.A[2],
                SERDINP[1]: landpattern.A[3],
                SERDINN[1]: landpattern.A[4],
                SERDINP[2]: landpattern.A[5],
                SERDINN[2]: landpattern.A[6],
                SERDINP[3]: landpattern.A[7],
                SERDINN[3]: landpattern.A[8],
                # SYNC~
                SYNCP: landpattern.B[1],
                SYNCN: landpattern.B[2],
                # SYSREF
                SYSREFP: landpattern.B[3],
                SYSREFN: landpattern.B[4],
                # DEVCLK
                DEVCLKP: landpattern.B[5],
                DEVCLKN: landpattern.B[6],
            }
        )
    ]

    pin_models = []
    for i in range(4):
        pin_models.append(TerminatingPinModel(SERDINP[i], delay=10.0e-15, loss=0.1))
        pin_models.append(TerminatingPinModel(SERDINN[i], delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(SYNCP, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(SYNCN, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(SYSREFP, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(SYSREFN, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(DEVCLKP, delay=10.0e-15, loss=0.1))
    pin_models.append(TerminatingPinModel(DEVCLKN, delay=10.0e-15, loss=0.1))

    symbol = BoxSymbol()


class JESD204FPGACircuit(Circuit):
    """JESD204 FPGA Circuit with Provide for Port Assignment

    Wraps the FPGA component and provides a 4-lane JESD204 port
    through the Provide mechanism.
    """

    def __init__(self):
        self.fpga = JESD204FPGAComponent()

        self.jesd_port = Provide(
            JESD204(JESD204LaneCount.x4)
        ).one_of(lambda b: [self._create_mapping(b)])

    def _create_mapping(self, b: JESD204) -> dict:
        mapping = {}

        # Map data lanes (bundle lane → FPGA SERDIN)
        for i in range(len(b.lane)):
            mapping[b.lane[i].p] = self.fpga.SERDINP[i]
            mapping[b.lane[i].n] = self.fpga.SERDINN[i]

        # Map SYNC~ (FPGA SYNC output → bundle SYNC)
        if b.SYNC is not None:
            mapping[b.SYNC.p] = self.fpga.SYNCP
            mapping[b.SYNC.n] = self.fpga.SYNCN

        # Map SYSREF
        if b.SYSREF is not None:
            mapping[b.SYSREF.p] = self.fpga.SYSREFP
            mapping[b.SYSREF.n] = self.fpga.SYSREFN

        # Map DEVCLK
        if b.DEVCLK is not None:
            mapping[b.DEVCLK.p] = self.fpga.DEVCLKP
            mapping[b.DEVCLK.n] = self.fpga.DEVCLKN

        return mapping
