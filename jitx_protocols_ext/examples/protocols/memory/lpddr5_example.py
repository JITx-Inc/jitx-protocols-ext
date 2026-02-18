"""LPDDR5 Protocol Example

Translation using Micron MT62F4G32D8DV-026_AIT_B memory component.

This example demonstrates:
1. LPDDR5 memory component with direct LPDDR5 port (not Provide)
2. Generic controller component with Provide() for pin optionality
3. LPDDR5 x32 DualRank configuration
4. Signal integrity constraints from LPDDR5Constraint
"""

from jitx import Design, Net
from jitx.circuit import Circuit

from ....common.example_board import ExampleBoard, ExampleSubstrate
from ....protocols.memory.lpddr5 import LPDDR5, LPDDR5Constraint, LPDDR5Rank, LPDDR5Width
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

        # Power nets
        self.power_nets = [
            self.GND + self.memory.pwr.Vn + self.controller.pwr.Vn,
            self.VDD + self.memory.pwr.Vp + self.controller.pwr.Vp,
        ]

        # Get LPDDR5 ports:
        # - Controller uses require() since it has Provide
        # - Memory uses direct io port since it has fixed connections
        ctrl_io = self.controller.require(LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank))
        mem_io = self.memory.io

        # Connect LPDDR5 interface with constraints
        topos = []

        with self.constraint.constrain_topology(
            ctrl_io, mem_io  # Controller -> Memory
        ) as (src, dst):
            # Reset signal (shared)
            topos.append([src.reset_n >> dst.reset_n])

            # Connect each channel (x32 = 2 channels)
            num_ch = 2
            num_ranks = 2
            for ch_idx in range(num_ch):
                # CK connection
                topos.append([src.ck[ch_idx] >> dst.ck[ch_idx]])

                # CS connections (2 ranks)
                for rank_idx in range(num_ranks):
                    topos.append([src.cs[ch_idx][rank_idx] >> dst.cs[ch_idx][rank_idx]])

                # CA connections (7 per channel)
                for ca_idx in range(7):
                    topos.append([src.ca[ch_idx][ca_idx] >> dst.ca[ch_idx][ca_idx]])

                # Data lane connections (2 lanes per channel)
                for lane_idx in range(2):
                    src_lane = src.d[ch_idx][lane_idx]
                    dst_lane = dst.d[ch_idx][lane_idx]

                    # WCK
                    topos.append([src_lane.wck >> dst_lane.wck])

                    # RDQS
                    topos.append([src_lane.rdqs >> dst_lane.rdqs])

                    # DQ (8 per lane)
                    for dq_idx in range(8):
                        topos.append([src_lane.dq[dq_idx] >> dst_lane.dq[dq_idx]])

                    # DMI
                    topos.append([src_lane.dmi >> dst_lane.dmi])

        self.lpddr5_topos = topos


class LPDDR5ExampleDesign(Design):
    """Complete LPDDR5 Example Design"""

    substrate = ExampleSubstrate()
    circuit = LPDDR5ExampleCircuit()
    board = ExampleBoard()
