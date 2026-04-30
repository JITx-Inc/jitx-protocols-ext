"""LPDDR5 Protocol Example

Translation using Micron MT62F4G32D8DV-026_AIT_B memory component.

This example demonstrates:
1. LPDDR5 memory component with Provide() for pin optionality
2. Generic controller component with Provide() for pin optionality
3. LPDDR5 x32 DualRank configuration
4. Signal integrity constraints from LPDDR5Constraint
"""

from jitx import Design, Net
from jitx.circuit import Circuit

from examples.common.generic_fr4_board import ExampleBoard, ExampleSubstrate
from jitx_protocols_ext.protocols.memory.lpddr5 import (
    LPDDR5,
    LPDDR5Constraint,
    LPDDR5Rank,
    LPDDR5Width,
)
from jitx_protocols_ext.protocols.memory.lpddr_constraints import (
    get_H,
    make_lpddr_spacing_rules,
    tag_lpddr_link,
)

from .lpddr5_components import LPDDR5ControllerCircuit
from .MT62F4G32D8DV_026_AIT_B import LPDDR5MemoryCircuit


class LPDDR5ExampleCircuit(Circuit):
    """LPDDR5 Example Circuit

    Connects Micron MT62F4G32D8DV-026_AIT_B memory to generic controller.

    LPDDR5 timing constraints:
    - CK to CS skew: ±4ps
    - CK to CA skew: ±4ps
    - CK to WCK/RDQS skew: -250ps to +1250ps
    - WCK/RDQS to DQ/DMI skew: ±2.5ps
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # Instantiate devices
        self.memory = LPDDR5MemoryCircuit()
        self.controller = LPDDR5ControllerCircuit()

        # LPDDR5 constraint setup
        self.constraint = LPDDR5Constraint(
            width=LPDDR5Width.x32,
            rank=LPDDR5Rank.DualRank,
        )

        # Power nets — memory has 4 separate rails, all sharing VSS
        self.GND += self.memory.pwr_vdd1.Vn + self.controller.pwr.Vn
        self.VDD += self.controller.pwr.Vp

        self.VDD1 = Net(name="VDD1")
        self.VDD1 += self.memory.pwr_vdd1.Vp

        self.VDD2H = Net(name="VDD2H")
        self.VDD2H += self.memory.pwr_vdd2h.Vp

        self.VDD2L = Net(name="VDD2L")
        self.VDD2L += self.memory.pwr_vdd2l.Vp

        self.VDDQ = Net(name="VDDQ")
        self.VDDQ += self.memory.pwr_vddq.Vp

        # Get LPDDR5 ports via require() — both use Provide
        ctrl_io = self.controller.require(LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank))
        mem_io = self.memory.require(LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank))

        # `tag_lpddr_link` builds all signal topologies via `>>` and tags
        # each one with its per-port-type, byte, and channel tags. The
        # AMD UG863 spacing rules registered below match those tags.
        with self.constraint.constrain_topology(
            ctrl_io,
            mem_io,  # Controller -> Memory
        ) as (src, dst):
            self.lpddr5_topos = tag_lpddr_link(
                src, dst, LPDDR5Width.x32, LPDDR5Rank.DualRank,
            )

        # AMD UG863 pairwise spacing rules — parameterized by H, the
        # distance from the inner stripline to its nearest GND plane.
        # The generic FR-4 stackup routes high-speed signals on its
        # inner layers (signal layer index 2 = first inner copper).
        h_mm = get_H(ExampleSubstrate.stackup, signal_layer_index=2)
        self.lpddr_rules = make_lpddr_spacing_rules(
            H=h_mm, num_bytes=4, num_channels=2,
        )


class LPDDR5ExampleDesign(Design):
    """Complete LPDDR5 Example Design"""

    substrate = ExampleSubstrate()
    circuit = LPDDR5ExampleCircuit()
    board = ExampleBoard()
