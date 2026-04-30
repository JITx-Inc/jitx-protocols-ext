"""LPDDR5 example using the Xilinx XC2VE3858 FPGA as the controller.

Replaces the generic `LPDDR5ControllerCircuit` from `lpddr5_example.py` with
the full 2112-pin XC2VE3858 part. The FPGA exposes 5 LPDDR5 providers (one
per DDR memory controller) — `require()` will pick the first that fits with
one of three packing options (Optimum / PackedLeft / PackedRight).
"""

from jitx import Design, Net
from jitx.circuit import Circuit
from jitx.copper import Pour
from jitx.transform import Transform

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
    attach_lpddr_link_vias,
    drop_vias_on_net_pads,
    get_H,
    make_lpddr_routing_rules,
    make_lpddr_spacing_rules,
    tag_lpddr_link,
)

from .MT62F4G32D8DV_026_AIT_B import MT62F4G32D8DV_026_AIT_B, LPDDR5MemoryCircuit
from .xc2ve3858_components import (
    LPDDR5Packing,
    X5IO_DDRMC_BASE_BANKS,
    XC2VE3858,
    XC2VE3858Circuit,
)


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

# LPDDR5 bus-signal via attachments — one via per port per side via
# `PortAttachment`. Each byte lane gets a single Via type that covers
# every signal in that byte (DQ[7:0], DMI, WCK_p/n, RDQS_p/n — 13
# ports per side). Each channel gets a single Via type for its CAC
# signals (CK_p/n, CS[0..rank-1], CA[0..6]). The same Via class is
# applied on both controller (FPGA) and memory sides. Type duplication
# is fine — only 3 inner-stripline BGA-escape uvias exist on the
# HighPerfSubstrate (L1→L3, L1→L5, L1→L7), so byte lanes and channels
# fan out to the same set of routing layers.
#
# Index convention: byte_idx = ch_idx * 2 + lane_idx
#   byte 0 = channel 0 low byte (DQ[7:0])
#   byte 1 = channel 0 high byte (DQ[15:8])
#   byte 2 = channel 1 low byte
#   byte 3 = channel 1 high byte
LPDDR5_BYTE_VIA_TYPES: list[type] = [
    HighPerfSubstrate.uVia_L1_L3,  # byte 0 → L3
    HighPerfSubstrate.uVia_L1_L5,  # byte 1 → L5
    HighPerfSubstrate.uVia_L1_L3,  # byte 2 → L3 (reuse top-shallowest)
    HighPerfSubstrate.uVia_L1_L5,  # byte 3 → L5
]
LPDDR5_CHANNEL_VIA_TYPES: list[type] = [
    HighPerfSubstrate.uVia_L1_L7,  # channel 0 CAC → L7
    HighPerfSubstrate.uVia_L1_L7,  # channel 1 CAC → L7 (reuse)
]
LPDDR5_RESET_VIA: type = HighPerfSubstrate.uVia_L1_L7


# 0-indexed conductor layers that should carry a board-wide GND pour.
# In the 16-layer HighPerfStackup these are exactly the dedicated GND
# planes (L2, L4, L6, L8 above d_center; L9, L11, L13, L15 below).
GND_POUR_LAYERS: tuple[int, ...] = (1, 3, 5, 7, 8, 10, 12, 14)


class XC2VE3858LPDDR5ExampleCircuit(Circuit):
    """LPDDR5 link from XC2VE3858 FPGA to a Micron LPDDR5X DRAM."""

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # Mark this circuit as free-floating so the via instances we
        # create at this level live in the *board* (root) frame rather
        # than this circuit's local frame. Without this, JITX
        # interprets per-via `.at(transform)` calls relative to the
        # enclosing circuit, and the via drops below — which we built
        # in board coordinates from the child placement transforms —
        # end up double-transformed once the design is laid out.
        self.at(floating=True)

        # Explicit child placement via `self.place(...)` — the
        # canonical Circuit API for fixing a child at a known transform
        # on this circuit's frame of reference. The vias below are
        # placed in board coordinates (JITX vias don't inherit a
        # parent container's transform), so the via-drop call is given
        # the same transform.
        self.fpga = XC2VE3858Circuit()
        self.memory = LPDDR5MemoryCircuit()
        fpga_tx = Transform.translate(0.0, 0.0)
        mem_tx = Transform.translate(30.0, 0.0)
        self.place(self.fpga, fpga_tx)
        self.place(self.memory, mem_tx)

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
        self.constraint = LPDDR5Constraint(
            width=LPDDR5Width.x32,
            rank=LPDDR5Rank.DualRank,
        )

        ctrl_io = self.fpga.require(LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank))
        mem_io = self.memory.require(LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank))

        with self.constraint.constrain_topology(ctrl_io, mem_io) as (src, dst):
            self.lpddr5_topos = tag_lpddr_link(
                src, dst, LPDDR5Width.x32, LPDDR5Rank.DualRank,
            )

        # Per-port via attachments on the LPDDR5 bus. Bundle leaves
        # all share one underlying Port object via JITX's pin-assignment
        # system, so we explicitly build the {logical_leaf →
        # physical_pin} map by reusing the wrapper circuits' Provide-
        # mapping methods. The (base_bank, packing) tuple must match
        # the option the solver actually picks — JITX's pin-assignment
        # solver chose base_bank=713 (the last DDRMC, X5IO_DDRMC_BASE_BANKS[-1])
        # with the OPTIMUM packing for this design; if you constrain
        # the solver differently, update this call.
        ctrl_resolution_map = self.fpga._build_lpddr5_mapping(
            ctrl_io,
            base_bank=X5IO_DDRMC_BASE_BANKS[-1],
            packing=LPDDR5Packing.OPTIMUM,
        )
        mem_resolution_map = self.memory._create_lpddr5_mapping(mem_io)

        self.lpddr5_via_attachments = attach_lpddr_link_vias(
            ctrl_io, mem_io,
            LPDDR5Width.x32, LPDDR5Rank.DualRank,
            byte_via_types=LPDDR5_BYTE_VIA_TYPES,
            channel_via_types=LPDDR5_CHANNEL_VIA_TYPES,
            reset_via=LPDDR5_RESET_VIA,
            ctrl_component_instance=self.fpga,
            mem_component_instance=self.memory,
            ctrl_resolution_map=ctrl_resolution_map,
            mem_resolution_map=mem_resolution_map,
            ctrl_parent_transform=fpga_tx,
            mem_parent_transform=mem_tx,
        )

        # AMD UG863 pairwise spacing rules — parameterized by H, the
        # distance from the inner stripline (signal layer index 2 of the
        # 16-layer symmetric stack) to its nearest GND plane.
        h_mm = get_H(HighPerfSubstrate.stackup, signal_layer_index=2)
        self.lpddr_spacing_rules = make_lpddr_spacing_rules(
            H=h_mm, num_bytes=4, num_channels=2,
        )

        # Tag-based design rules that mimic an inner-stripline routing
        # structure (trace width per signal class + within-pair P/N
        # spacing for each diff signal). Numeric values pulled from
        # high_perf_board's published trace dimensions so this example
        # tracks the substrate's geometry without re-stating impedances.
        self.lpddr_routing_rules = make_lpddr_routing_rules(
            dq_trace_width=INNER_SE_40_TRACE_WIDTH,
            ca_trace_width=INNER_SE_40_TRACE_WIDTH,
            diff_trace_width=INNER_DIFF_75_TRACE_WIDTH,
            diff_pair_spacing=INNER_DIFF_75_PAIR_SPACING,
        )

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
            parent_transform=fpga_tx,
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
            parent_transform=mem_tx,
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
