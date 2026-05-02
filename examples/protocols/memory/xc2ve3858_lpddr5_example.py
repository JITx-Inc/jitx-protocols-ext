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

from examples.common.high_perf_board import (
    INNER_DIFF_75_PAIR_SPACING,
    INNER_DIFF_75_TRACE_WIDTH,
    INNER_SE_40_TRACE_WIDTH,
    HighPerfBoard,
    HighPerfSubstrate,
)
from jitx_protocols_ext.protocols.memory.lpddr5 import (
    LPDDR5,
    LPDDR5Constraint,
    LPDDR5Rank,
    LPDDR5Width,
)
from jitx_protocols_ext.protocols.memory.lpddr_constraints import (
    drop_vias_on_net_pads,
    get_H,
    make_lpddr_routing_rules,
    make_lpddr_spacing_rules,
    tag_lpddr_link,
)

from .MT62F4G32D8DV_026_AIT_B import MT62F4G32D8DV_026_AIT_B, LPDDR5MemoryCircuit
from .xc2ve3858_components import XC2VE3858, XC2VE3858Circuit


# Per-net via-on-pad drops for the FPGA side of this design. Each
# entry maps a net name to the Via class that should be dropped on
# every pad of that net. The same TH_Via_Pwr type is used for GND and
# every supply rail — ground stitching and power-pin escapes share the
# same via geometry.
FPGA_NET_VIA_DROPS: dict[str, type] = {
    "GND": HighPerfSubstrate.TH_Via_Pwr,
    "VDD": HighPerfSubstrate.TH_Via_Pwr,
    "VCC_SOC": HighPerfSubstrate.TH_Via_Pwr,
    "VCC_AIE": HighPerfSubstrate.TH_Via_Pwr,
    "VCC_FPD": HighPerfSubstrate.TH_Via_Pwr,
    "VCCAUX": HighPerfSubstrate.TH_Via_Pwr,
    "VCC_RAM": HighPerfSubstrate.TH_Via_Pwr,
    "VCC_MMD": HighPerfSubstrate.TH_Via_Pwr,
}

# Memory-side via drops: GND plus every DRAM supply rail. Same
# `TH_Via_Pwr` body for all of them so each ball pad gets a direct
# stitch to its reference plane on the inner layers.
MEM_NET_VIA_DROPS: dict[str, type] = {
    "GND": HighPerfSubstrate.TH_Via_Pwr,
    "VDD1": HighPerfSubstrate.TH_Via_Pwr,
    "VDD2H": HighPerfSubstrate.TH_Via_Pwr,
    "VDD2L": HighPerfSubstrate.TH_Via_Pwr,
    "VDDQ": HighPerfSubstrate.TH_Via_Pwr,
}

# 0-indexed conductor layers that should carry a board-wide GND pour.
# In the 16-layer HighPerfStackup these are exactly the dedicated GND
# planes (L2, L4, L6, L8 above d_center; L9, L11, L13, L15 below).
GND_POUR_LAYERS: tuple[int, ...] = (1, 3, 5, 7, 8, 10, 12, 14)


class XC2VE3858LPDDR5ExampleCircuit(Circuit):
    """LPDDR5 link from XC2VE3858 FPGA to a Micron LPDDR5X DRAM."""

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # Wrapper circuit floats so the via drops below live in the
        # board (root) frame rather than this circuit's local frame.
        self.at(floating=True)

        # FPGA and memory are also free-floating — final placement is
        # determined by the layout backend rather than fixed here.
        self.fpga = XC2VE3858Circuit()
        self.memory = LPDDR5MemoryCircuit()
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

        # Structure-free LPDDR5 routing path:
        # 1. `LPDDR5Constraint` (no structure params) enforces skew + per-
        #    topology insertion loss via `constrain_topology`.
        # 2. `tag_lpddr_link` labels each topology with signal-type /
        #    byte / channel tags.
        # 3. `make_lpddr_routing_rules` and `make_lpddr_spacing_rules`
        #    generate the tag-based `design_constraint` rules for trace
        #    width / pair spacing / clearance — replacing the per-layer
        #    bindings that a `RoutingStructure` would normally provide.
        # Pair the per-signal-class routing structures with the
        # constraint. SE_40 covers DQ + DMI + CA + CSn + RESET_N
        # (40 Ω single-ended per AMD UG863). DRS_DiffPair_75 is shared
        # by CK / WCK / RDQS (75 Ω diff). The structures' clearance
        # values are H-derived (UG863 H-multiplier rules); the tag-
        # based design rules from `make_lpddr_routing_rules` /
        # `make_lpddr_spacing_rules` layer on cross-class clearances
        # the per-layer structure clearance can't express.
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
        mem_io = self.memory.require(LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank))

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

        # Tag-based design rules — currently disabled. The LPDDR5
        # routing structures bound on `LPDDR5Constraint` above already
        # set per-layer trace width / pair spacing / clearance, so
        # we don't layer the tag rules on top right now. The helper
        # calls below are kept as reference for re-enabling them
        # alongside `tag_lpddr_link` (see the `constrain_topology`
        # block above).
        #
        # h_mm = get_H(HighPerfSubstrate.stackup, signal_layer_index=2)
        # self.lpddr_spacing_rules = make_lpddr_spacing_rules(
        #     H=h_mm, num_bytes=4, num_channels=2,
        # )
        # self.lpddr_routing_rules = make_lpddr_routing_rules(
        #     dq_trace_width=INNER_SE_40_TRACE_WIDTH,
        #     ca_trace_width=INNER_SE_40_TRACE_WIDTH,
        #     diff_trace_width=INNER_DIFF_75_TRACE_WIDTH,
        #     diff_pair_spacing=INNER_DIFF_75_PAIR_SPACING,
        # )

        # Drop vias on every power/ground pad of the FPGA and on every
        # GND pad of the memory device, connecting each via into the
        # corresponding net so the layout engine actually emits them.
        # `via_in_pad` is enabled on `TH_Via_Pwr` so the via sits
        # directly inside the BGA ball pad, giving the shortest
        # possible reference-plane stitch (GND) or supply drop
        # (VDD / VCC_SOC / VCC_AIE).
        # Pad positions are read by introspection on the live
        # landpattern (no analytical row/col/pitch math), so adding
        # another rail only needs another `net_via_map` entry plus the
        # matching ports list — no geometry parameters.
        self.fpga_via_drops = drop_vias_on_net_pads(
            self.fpga,
            FPGA_NET_VIA_DROPS,
            {
                "GND": [*XC2VE3858.GND, *XC2VE3858.RSVDGND],
                "VDD": [*XC2VE3858.VCCINT],
                "VCC_SOC": [*XC2VE3858.VCC_SOC],
                "VCC_AIE": [*XC2VE3858.VCC_AIE],
                "VCC_FPD": [*XC2VE3858.VCC_FPD],
                "VCCAUX": [*XC2VE3858.VCCAUX],
                "VCC_RAM": [*XC2VE3858.VCC_RAM],
                "VCC_MMD": [*XC2VE3858.VCC_MMD],
            },
            {
                "GND": self.GND,
                "VDD": self.VDD,
                "VCC_SOC": self.VCC_SOC,
                "VCC_AIE": self.VCC_AIE,
                "VCC_FPD": self.VCC_FPD,
                "VCCAUX": self.VCCAUX,
                "VCC_RAM": self.VCC_RAM,
                "VCC_MMD": self.VCC_MMD,
            },
        )
        self.mem_via_drops = drop_vias_on_net_pads(
            self.memory,
            MEM_NET_VIA_DROPS,
            {
                "GND": [*MT62F4G32D8DV_026_AIT_B.VSS],
                "VDD1": [*MT62F4G32D8DV_026_AIT_B.VDD1],
                "VDD2H": [*MT62F4G32D8DV_026_AIT_B.VDD2H],
                "VDD2L": [*MT62F4G32D8DV_026_AIT_B.VDD2L],
                "VDDQ": [*MT62F4G32D8DV_026_AIT_B.VDDQ],
            },
            {
                "GND": self.GND,
                "VDD1": self.VDD1,
                "VDD2H": self.VDD2H,
                "VDD2L": self.VDD2L,
                "VDDQ": self.VDDQ,
            },
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
