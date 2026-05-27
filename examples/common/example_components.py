"""Common Example Components for Protocol Examples

Translation of jsl/examples/protocols/common/example-components.stanza

These components are designed to be used in SI-constrained topologies.
They have pin models defined to allow SI constraints to propagate correctly.
"""

from jitx.component import Component
from jitx.net import Port
from jitx.si import BridgingPinModel
from jitxlib.landpatterns.twopin.smt import SMT
from jitxlib.symbols.capacitor import CapacitorSymbol
from jitxlib.symbols.resistor import ResistorSymbol


class BlockingCapLandpattern(SMT):
    """0201 Landpattern for blocking capacitor"""

    def __init__(self):
        super().__init__("0201")


class PullUpResLandpattern(SMT):
    """0201 Landpattern for pull-up resistor"""

    def __init__(self):
        super().__init__("0201")


class BlockingCapacitor(Component):
    """Blocking Capacitor for SI Topologies

    Translation of block-cap from example-components.stanza.

    This component is used for AC coupling in high-speed differential
    topologies like PCIe TX paths. It has pin models defined to allow
    SI constraints to propagate through correctly.

    Args:
        capacitance: Capacitance value in Farads (default: 220nF)
    """

    manufacturer = "KYOCERA AVX"
    mpn = "02016D224MAT2A"
    datasheet = "http://datasheets.avx.com/cx5r.pdf"
    reference_prefix = "C"
    description = "Blocking capacitor for high-speed differential pairs"

    p1 = Port()
    p2 = Port()

    symbol = CapacitorSymbol()
    landpattern = BlockingCapLandpattern()
    pad_mapping = {p1: "p1", p2: "p2"}

    # Pin model allows SI constraints to propagate through this component
    # Values are placeholders - real values depend on actual component
    pin_model = BridgingPinModel(p1, p2, delay=0.0, loss=0.0)

    def __init__(self, capacitance: float = 220.0e-9):
        self.capacitance = capacitance


class PullUpResistor(Component):
    """Pull-up Resistor for SI Topologies

    Translation of pu-res from example-components.stanza.

    This component is used for pull-up resistors on control signals.
    It has pin models defined to allow SI constraints to propagate
    through correctly.

    Args:
        resistance: Resistance value in Ohms (default: 10k)
    """

    manufacturer = "KYOCERA AVX"
    mpn = "02016D224MAT2A"
    datasheet = "http://datasheets.avx.com/cx5r.pdf"
    reference_prefix = "R"
    description = "Pull-up resistor"

    p1 = Port()
    p2 = Port()

    symbol = ResistorSymbol()
    landpattern = PullUpResLandpattern()
    pad_mapping = {p1: "p1", p2: "p2"}

    # Pin model allows SI constraints to propagate through this component
    pin_model = BridgingPinModel(p1, p2, delay=0.0, loss=0.0)

    def __init__(self, resistance: float = 10.0e3):
        self.resistance = resistance
