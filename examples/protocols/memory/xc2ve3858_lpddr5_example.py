"""LPDDR5 example using the Xilinx XC2VE3858 FPGA as the controller.

Replaces the generic `LPDDR5ControllerCircuit` from `lpddr5_example.py` with
the full 2112-pin XC2VE3858 part. The FPGA exposes 5 LPDDR5 providers (one
per DDR memory controller) — `require()` will pick the first that fits with
one of three packing options (Optimum / PackedLeft / PackedRight).
"""

from jitx import Design, Net
from jitx.circuit import Circuit
from jitx.copper import Pour
from jitx.si import ReferencePlanes

from examples.common.high_perf_board import HighPerfBoard, HighPerfSubstrate
from jitx_protocols_ext.protocols.memory.lpddr5 import (
    LPDDR5,
    LPDDR5Constraint,
    LPDDR5Rank,
    LPDDR5Width,
)
from jitx_protocols_ext.protocols.memory.lpddr_constraints import tag_lpddr_link

from .MT62F4G32D8DV_026_AIT_B import LPDDR5MemoryCircuit
from .xc2ve3858_components import XC2VE3858Circuit


# 0-indexed conductor layers that should carry a board-wide GND pour.
# In the 20-layer HighPerfStackup these are exactly the dedicated GND
# planes (L2, L4, L6, L8, L10 above d_center; L11, L13, L15, L17, L19 below).
GND_POUR_LAYERS: tuple[int, ...] = (1, 3, 5, 7, 9, 10, 12, 14, 16, 18)


class XC2VE3858LPDDR5ExampleCircuit(Circuit):
    """LPDDR5 link from XC2VE3858 FPGA to a Micron LPDDR5X DRAM."""

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # FPGA and memory are free-floating — final placement is set
        # by the user / layout backend. Power/ground via drops happen
        # inside each wrapper (via `power_via=`) so the vias travel
        # with whichever placement is chosen.
        #
        # Memory signal-pad vias select fanout layer per AMD UG863:
        #   byte 0 (Ch A low)  → uVia_L1_L5
        #   byte 1 (Ch A high) → uVia_L1_L3
        #   byte 2 (Ch B low)  → uVia_L1_L5
        #   byte 3 (Ch B high) → uVia_L1_L3
        #   CAC Ch A (CK/CS/CA_A) → uVia_L1_L7
        #   CAC Ch B (CK/CS/CA_B) → uVia_L1_L9
        #   RESET_N               → uVia_L1_L9
        self.fpga = XC2VE3858Circuit(power_via=HighPerfSubstrate.TH_Via_Pwr)
        self.memory = LPDDR5MemoryCircuit(
            power_via=HighPerfSubstrate.TH_Via_Pwr,
            byte_via_types=[
                HighPerfSubstrate.uVia_L1_L5,  # byte 0: Ch A low
                HighPerfSubstrate.uVia_L1_L3,  # byte 1: Ch A high
                HighPerfSubstrate.uVia_L1_L5,  # byte 2: Ch B low
                HighPerfSubstrate.uVia_L1_L3,  # byte 3: Ch B high
            ],
            cac_via_types=[
                HighPerfSubstrate.uVia_L1_L7,  # CAC Channel A
                HighPerfSubstrate.uVia_L1_L9,  # CAC Channel B
            ],
            reset_via=HighPerfSubstrate.uVia_L1_L7,
        )
        self.fpga.at(floating=True)
        self.memory.at(floating=True)

        # Ground shared across FPGA + every memory rail. The FPGA exposes
        # one Power port per rail; their Vn pins are merged inside the
        # circuit's main GND net, so any rail's Vn here pulls the rest in.
        self.GND += (
            self.fpga.pwr_vccint.Vn
            + self.memory.pwr_vdd1.Vn
            + self.memory.pwr_vdd2h.Vn
            + self.memory.pwr_vdd2l.Vn
            + self.memory.pwr_vddq.Vn
        )
        self.VDD += self.fpga.pwr_vccint.Vp
        self.VCC_SOC = Net(name="VCC_SOC") + self.fpga.pwr_vcc_soc.Vp
        self.VCC_AIE = Net(name="VCC_AIE") + self.fpga.pwr_vcc_aie.Vp
        self.VCC_FPD = Net(name="VCC_FPD") + self.fpga.pwr_vcc_fpd.Vp
        self.VCCAUX = Net(name="VCCAUX") + self.fpga.pwr_vccaux.Vp
        self.VCC_RAM = Net(name="VCC_RAM") + self.fpga.pwr_vcc_ram.Vp
        self.VCC_MMD = Net(name="VCC_MMD") + self.fpga.pwr_vcc_mmd.Vp

        self.VDD1 = Net(name="VDD1") + self.memory.pwr_vdd1.Vp
        self.VDD2H = Net(name="VDD2H") + self.memory.pwr_vdd2h.Vp
        self.VDD2L = Net(name="VDD2L") + self.memory.pwr_vdd2l.Vp
        self.VDDQ = Net(name="VDDQ") + self.memory.pwr_vddq.Vp

        # Per-signal-class routing structures bound on the LPDDR5
        # constraint. SE_40 covers DQ + DMI + CA + CSn + RESET_N
        # (40 Ω single-ended per AMD UG863). DRS_DiffPair_75 is shared
        # by CK / WCK / RDQS (75 Ω diff). Per-layer trace width /
        # spacing / clearance are baked into the structures themselves.
        self.constraint = LPDDR5Constraint(
            width=LPDDR5Width.x32,
            rank=LPDDR5Rank.DualRank,
            dq_structure=HighPerfSubstrate.SE_40,
            ca_structure=HighPerfSubstrate.SE_40,
            ck_structure=HighPerfSubstrate.DRS_DiffPair_75,
            wck_structure=HighPerfSubstrate.DRS_DiffPair_75,
            rdqs_structure=HighPerfSubstrate.DRS_DiffPair_75,
        )

        ctrl_io = self.fpga.require(LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank))
        # Memory exposes a fixed-mapping `lpddr5` bundle directly; no
        # require() needed because there is no pin-assignment choice
        # on the DRAM side.
        mem_io = self.memory.lpddr5

        # `ReferencePlanes(self.GND)` (all-form) tells JITX that every
        # reference-layer slot demanded by the LPDDR5 routing
        # structures (8 GND planes in the 16-layer stripline stackup)
        # resolves to this circuit's GND net.
        with ReferencePlanes(self.GND):
            with self.constraint.constrain_topology(ctrl_io, mem_io) as (src, dst):
                # `tag_lpddr_link` is the canonical helper that builds
                # `src.X >> dst.X` TopologyNets for every LPDDR5 signal
                # AND tags them. The `>>` connections are required —
                # without them the require()'d bundles never form
                # topologies, and constraint translation fails to map
                # the bundle leaves back to this circuit (manifests as
                # an "is not an ancestor of child <<<<Port>>>>" error).
                self.lpddr5_topos = tag_lpddr_link(
                    src, dst, LPDDR5Width.x32, LPDDR5Rank.DualRank,
                )

        # Board-wide GND pours on every dedicated GND plane layer of
        # the 16-layer HighPerfStackup. Pour shape matches the board
        # outline; isolation is left at 0 so the global fab rules
        # decide the clearance to other nets.
        self.gnd_pours = [
            Pour(HighPerfBoard.shape, layer=layer)
            for layer in GND_POUR_LAYERS
        ]
        for pour in self.gnd_pours:
            self.GND += pour


class XC2VE3858LPDDR5ExampleDesign(Design):
    """Complete XC2VE3858 + LPDDR5X example design.

    Uses the high-performance HDI substrate by default — the LPDDR5
    timing budget benefits from inner-stripline routing and a low-loss
    dielectric. Override `substrate` / `board` to swap to a different
    stackup (e.g. `ExampleSubstrate` / `ExampleBoard` for the baseline
    FR-4 substrate).
    """

    substrate = HighPerfSubstrate()
    circuit = XC2VE3858LPDDR5ExampleCircuit()
    board = HighPerfBoard()
