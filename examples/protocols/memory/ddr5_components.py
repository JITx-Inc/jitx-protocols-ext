"""DDR5 Example Components

Micron DDR5 x16 SDRAM component (MT60B2G8HB-48B) copied from the JITx-Inc/demo
repository, plus a dummy controller component and circuit wrappers that expose
DDR5 protocol bundle ports.

Component:
    DDR5Memory -- 96-ball FBGA (0.5mm pitch), 8x14 grid with depopulated
    edge columns, two byte lanes (lower DQ[0:7], upper DQ[8:15]).
"""

import jitx
from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.net import Port, Provide
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.grid_layout import GridPosition
from jitxlib.landpatterns.grid_planner import GridPlanner
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row

from jitx_protocols_ext.protocols.memory.ddr5 import DDR5, DDR5Rank, DDR5Width

# =============================================================================
# Grid Planner -- depopulated positions for 96-ball FBGA
# =============================================================================

# 8 rows (A-H) x 14 columns = 112 positions, 16 depopulated = 96 active.
# Columns 1 and 14 are depopulated across all rows.
# 0-indexed: col 0 and col 13 for all 8 rows.
_INACTIVE_POSITIONS = frozenset((r, c) for r in range(8) for c in (0, 13))


class DDR5GridPlanner(GridPlanner):
    """Grid planner that removes columns 1 and 14 for 96-ball FBGA."""

    def is_active(self, pos: GridPosition, num_rows: int, num_cols: int) -> bool | None:
        if (pos.row, pos.column) in _INACTIVE_POSITIONS:
            return False
        return None


# =============================================================================
# DDR5 Memory Component (from JITx-Inc/demo)
# =============================================================================


class DDR5Memory(jitx.Component):
    """Micron DDR5 x16 SDRAM in 96-ball FBGA.

    Two byte lanes (lower DQ[0:7], upper DQ[8:15]), each with its own
    differential data strobe and data mask/DBI pin.

    96 balls: 44 signal + 52 power/ground.
    """

    mpn = "MT60B2G8HB-48B"
    manufacturer = "Micron"
    reference_designator_prefix = "U"
    datasheet = "https://www.micron.com/products/memory/dram-components/ddr5-sdram"

    # -----------------------------------------------------------------
    # Data -- Byte Lane 0 (lower)
    # -----------------------------------------------------------------
    DQ_L = [Port() for _ in range(8)]  # DQ[0:7]
    DQS0_t = Port()  # Data strobe 0 true
    DQS0_c = Port()  # Data strobe 0 complement
    DMI0 = Port()  # DM0 / DBI0

    # -----------------------------------------------------------------
    # Data -- Byte Lane 1 (upper)
    # -----------------------------------------------------------------
    DQ_U = [Port() for _ in range(8)]  # DQ[8:15]
    DQS1_t = Port()  # Data strobe 1 true
    DQS1_c = Port()  # Data strobe 1 complement
    DMI1 = Port()  # DM1 / DBI1

    # -----------------------------------------------------------------
    # Command / Address
    # -----------------------------------------------------------------
    CA = [Port() for _ in range(14)]  # CA[0:13]
    CK_t = Port()  # Differential clock true
    CK_c = Port()  # Differential clock complement
    CS_n = Port()  # Chip select (active low)
    CKE = Port()  # Clock enable
    ODT = Port()  # On-die termination
    RESET_n = Port()  # Reset (active low)

    # -----------------------------------------------------------------
    # Miscellaneous
    # -----------------------------------------------------------------
    ALERT_n = Port()  # Alert output (active low)
    ZQ = Port()  # Impedance calibration

    # -----------------------------------------------------------------
    # Power (52 pins total)
    # -----------------------------------------------------------------
    VDD = [Port() for _ in range(15)]  # Core supply 1.1V
    VDDQ = [Port() for _ in range(9)]  # I/O supply 1.1V
    VSS = [Port() for _ in range(22)]  # Core ground
    VSSQ = [Port() for _ in range(6)]  # I/O ground

    def __init__(self):
        # Landpattern: 8 rows x 14 cols, 0.5mm pitch, 96 active balls
        self.landpattern = (
            BGA(
                num_rows=8,
                num_cols=14,
                pitch=0.50,
                ball_diameter=0.20,
            )
            .grid_planner(DDR5GridPlanner())
            .pad_config(SMDPadConfig(soldermask=0.025))
            .package_body(
                RectanglePackage(
                    width=Toleranced.min_max(12.9, 13.1),
                    length=Toleranced.min_max(7.9, 8.1),
                    height=Toleranced.min_max(1.1, 1.3),
                )
            )
        )

        # =============================================================
        # Multi-unit symbol
        # =============================================================

        # Data unit -- both byte lanes
        self.symbol_data = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    *self.DQ_L,
                    self.DQS0_t,
                    self.DQS0_c,
                    self.DMI0,
                ),
                right=PinGroup(
                    *self.DQ_U,
                    self.DQS1_t,
                    self.DQS1_c,
                    self.DMI1,
                ),
            ),
        )

        # Command/address unit
        self.symbol_cmd = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    *self.CA,
                ),
                right=PinGroup(
                    self.CK_t,
                    self.CK_c,
                    self.CS_n,
                    self.CKE,
                    self.ODT,
                    self.RESET_n,
                    self.ALERT_n,
                    self.ZQ,
                ),
            ),
        )

        # Power unit
        self.symbol_power = BoxSymbol(
            columns=Column(
                up=PinGroup(*self.VDD, *self.VDDQ),
                down=PinGroup(*self.VSS, *self.VSSQ),
            ),
        )

        # =============================================================
        # Pad mapping -- JEDEC DDR5 x16 96-ball FBGA
        # =============================================================
        # Rows A(bottom)..H(top), active columns 2..13 per row.

        lp = self.landpattern
        m: dict = {}

        # Row A: VSS DQ4 VSS DQ5 DQ6 DQ7 | DQ8 DQ9 DQ10 VSS DQ11 VSS
        m[self.VSS[0]] = lp.A[2]
        m[self.DQ_L[4]] = lp.A[3]
        m[self.VSS[1]] = lp.A[4]
        m[self.DQ_L[5]] = lp.A[5]
        m[self.DQ_L[6]] = lp.A[6]
        m[self.DQ_L[7]] = lp.A[7]
        m[self.DQ_U[0]] = lp.A[8]
        m[self.DQ_U[1]] = lp.A[9]
        m[self.DQ_U[2]] = lp.A[10]
        m[self.VSS[2]] = lp.A[11]
        m[self.DQ_U[3]] = lp.A[12]
        m[self.VSS[3]] = lp.A[13]

        # Row B: VDDQ DQS0c DQS0t VSSQ DMI0 VDDQ | VDDQ DMI1 VSSQ DQS1t DQS1c VDDQ
        m[self.VDDQ[0]] = lp.B[2]
        m[self.DQS0_c] = lp.B[3]
        m[self.DQS0_t] = lp.B[4]
        m[self.VSSQ[0]] = lp.B[5]
        m[self.DMI0] = lp.B[6]
        m[self.VDDQ[1]] = lp.B[7]
        m[self.VDDQ[2]] = lp.B[8]
        m[self.DMI1] = lp.B[9]
        m[self.VSSQ[1]] = lp.B[10]
        m[self.DQS1_t] = lp.B[11]
        m[self.DQS1_c] = lp.B[12]
        m[self.VDDQ[3]] = lp.B[13]

        # Row C: VSS DQ0 VSS DQ1 DQ2 DQ3 | DQ12 DQ13 DQ14 VSS DQ15 VSS
        m[self.VSS[4]] = lp.C[2]
        m[self.DQ_L[0]] = lp.C[3]
        m[self.VSS[5]] = lp.C[4]
        m[self.DQ_L[1]] = lp.C[5]
        m[self.DQ_L[2]] = lp.C[6]
        m[self.DQ_L[3]] = lp.C[7]
        m[self.DQ_U[4]] = lp.C[8]
        m[self.DQ_U[5]] = lp.C[9]
        m[self.DQ_U[6]] = lp.C[10]
        m[self.VSS[6]] = lp.C[11]
        m[self.DQ_U[7]] = lp.C[12]
        m[self.VSS[7]] = lp.C[13]

        # Row D: VDD CA0 CA1 VDD CA2 CA3 | CA4 CA5 VDD CA6 CA7 VDD
        m[self.VDD[0]] = lp.D[2]
        m[self.CA[0]] = lp.D[3]
        m[self.CA[1]] = lp.D[4]
        m[self.VDD[1]] = lp.D[5]
        m[self.CA[2]] = lp.D[6]
        m[self.CA[3]] = lp.D[7]
        m[self.CA[4]] = lp.D[8]
        m[self.CA[5]] = lp.D[9]
        m[self.VDD[2]] = lp.D[10]
        m[self.CA[6]] = lp.D[11]
        m[self.CA[7]] = lp.D[12]
        m[self.VDD[3]] = lp.D[13]

        # Row E: VSS CKc CKt VSS CA8 CA9 | CA10 CA11 VSS CA12 CA13 VSS
        m[self.VSS[8]] = lp.E[2]
        m[self.CK_c] = lp.E[3]
        m[self.CK_t] = lp.E[4]
        m[self.VSS[9]] = lp.E[5]
        m[self.CA[8]] = lp.E[6]
        m[self.CA[9]] = lp.E[7]
        m[self.CA[10]] = lp.E[8]
        m[self.CA[11]] = lp.E[9]
        m[self.VSS[10]] = lp.E[10]
        m[self.CA[12]] = lp.E[11]
        m[self.CA[13]] = lp.E[12]
        m[self.VSS[11]] = lp.E[13]

        # Row F: VDD CSn ALERTn VDD CKE ODT | RESETn VSSQ VDDQ VSSQ ZQ VDDQ
        m[self.VDD[4]] = lp.F[2]
        m[self.CS_n] = lp.F[3]
        m[self.ALERT_n] = lp.F[4]
        m[self.VDD[5]] = lp.F[5]
        m[self.CKE] = lp.F[6]
        m[self.ODT] = lp.F[7]
        m[self.RESET_n] = lp.F[8]
        m[self.VSSQ[2]] = lp.F[9]
        m[self.VDDQ[4]] = lp.F[10]
        m[self.VSSQ[3]] = lp.F[11]
        m[self.ZQ] = lp.F[12]
        m[self.VDDQ[5]] = lp.F[13]

        # Row G: VSS VDD VSS VDDQ VSS VDDQ | VSSQ VDDQ VSSQ VDD VSS VDDQ
        m[self.VSS[12]] = lp.G[2]
        m[self.VDD[6]] = lp.G[3]
        m[self.VSS[13]] = lp.G[4]
        m[self.VDDQ[6]] = lp.G[5]
        m[self.VSS[14]] = lp.G[6]
        m[self.VDDQ[7]] = lp.G[7]
        m[self.VSSQ[4]] = lp.G[8]
        m[self.VDDQ[8]] = lp.G[9]
        m[self.VSSQ[5]] = lp.G[10]
        m[self.VDD[7]] = lp.G[11]
        m[self.VSS[15]] = lp.G[12]
        m[self.VDD[8]] = lp.G[13]

        # Row H: VDD VSS VDD VSS VDD VSS | VDD VSS VDD VSS VDD VSS
        m[self.VDD[9]] = lp.H[2]
        m[self.VSS[16]] = lp.H[3]
        m[self.VDD[10]] = lp.H[4]
        m[self.VSS[17]] = lp.H[5]
        m[self.VDD[11]] = lp.H[6]
        m[self.VSS[18]] = lp.H[7]
        m[self.VDD[12]] = lp.H[8]
        m[self.VSS[19]] = lp.H[9]
        m[self.VDD[13]] = lp.H[10]
        m[self.VSS[20]] = lp.H[11]
        m[self.VDD[14]] = lp.H[12]
        m[self.VSS[21]] = lp.H[13]

        self.pad_mapping = PadMapping(m)


# =============================================================================
# DDR5 Memory Circuit -- wires DDR5 bundle to the physical component
# =============================================================================


class DDR5MemoryCircuit(Circuit):
    """DDR5 Memory Circuit

    Maps a DDR5 x16 bundle port to a single DDR5Memory component.
    Point-to-point topology for all signals.
    """

    io = DDR5(DDR5Width.x16, DDR5Rank.SingleRank)
    pwr = Power()
    pwr_q = Power()

    def __init__(self):
        self.mem = DDR5Memory()

        # Power connections
        pwr_net = self.pwr.Vp
        for vdd in self.mem.VDD:
            pwr_net = pwr_net + vdd
        self.vdd_net = pwr_net

        gnd_net = self.pwr.Vn
        for vss in self.mem.VSS:
            gnd_net = gnd_net + vss
        self.vss_net = gnd_net

        vddq_net = self.pwr_q.Vp
        for vddq in self.mem.VDDQ:
            vddq_net = vddq_net + vddq
        self.vddq_net = vddq_net

        vssq_net = self.pwr_q.Vn
        for vssq in self.mem.VSSQ:
            vssq_net = vssq_net + vssq
        self.vssq_net = vssq_net

        # ============================================================
        # DDR5 topology connections: bundle -> memory component
        # ============================================================
        topos = []

        # DQ -- lower byte lane
        for i in range(8):
            topos.append(self.io.data.DQ[i] >> self.mem.DQ_L[i])

        # DQ -- upper byte lane
        for i in range(8):
            topos.append(self.io.data.DQ[8 + i] >> self.mem.DQ_U[i])

        # DQS differential pairs
        topos.append(self.io.data.DQS[0].p >> self.mem.DQS0_t)
        topos.append(self.io.data.DQS[0].n >> self.mem.DQS0_c)
        topos.append(self.io.data.DQS[1].p >> self.mem.DQS1_t)
        topos.append(self.io.data.DQS[1].n >> self.mem.DQS1_c)

        # DMI signals
        topos.append(self.io.data.DMI[0] >> self.mem.DMI0)
        topos.append(self.io.data.DMI[1] >> self.mem.DMI1)

        # CA bus
        for i in range(14):
            topos.append(self.io.ca.CA[i] >> self.mem.CA[i])

        # CK differential pair
        topos.append(self.io.ca.CK.p >> self.mem.CK_t)
        topos.append(self.io.ca.CK.n >> self.mem.CK_c)

        # Control signals
        topos.append(self.io.ca.CS_n[0] >> self.mem.CS_n)
        topos.append(self.io.ca.CKE[0] >> self.mem.CKE)
        topos.append(self.io.ca.ODT[0] >> self.mem.ODT)
        topos.append(self.io.ca.RESET_n >> self.mem.RESET_n)
        topos.append(self.io.ca.ALERT_n >> self.mem.ALERT_n)

        self.topos = topos


# =============================================================================
# DDR5 Controller Component -- dummy controller with DDR5 interface pins
# =============================================================================


class DDR5ControllerBGALandpattern(BGA):
    """BGA Landpattern for DDR5 Controller Component"""

    def __init__(self):
        super().__init__(
            num_rows=20,
            num_cols=20,
            ball_diameter=0.40,
            pitch=0.65,
        )
        self.pad_config(SMDPadConfig())


_CTRL_REDUCED_ALPHA = "ABCDEFGHJKLMNPRTUVWY"


def _ctrl_row_name(idx: int) -> str:
    """Convert row index to BGA row name using JEDEC reduced alphabet."""
    if idx < len(_CTRL_REDUCED_ALPHA):
        return _CTRL_REDUCED_ALPHA[idx]
    first = idx // len(_CTRL_REDUCED_ALPHA) - 1
    second = idx % len(_CTRL_REDUCED_ALPHA)
    return _CTRL_REDUCED_ALPHA[first] + _CTRL_REDUCED_ALPHA[second]


class DDR5ControllerComponent(Component):
    """DDR5 Controller Component

    Dummy controller/SoC component with DDR5 x16 interface pins.
    """

    reference_designator_prefix = "U"
    mpn = "JITX-DDR5-CTRL"
    description = "Dummy DDR5 controller"

    # Data signals
    DQ = [Port() for _ in range(16)]
    DQS_P = [Port() for _ in range(2)]
    DQS_N = [Port() for _ in range(2)]
    DMI = [Port() for _ in range(2)]

    # Clock
    CK_P = Port()
    CK_N = Port()

    # Command/Address
    CA = [Port() for _ in range(14)]

    # Control signals
    CS_N = Port()
    CKE = Port()
    ODT = Port()
    RESET_N = Port()
    ALERT_N = Port()

    # Power
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(40)]
    VDDQ = [Port() for _ in range(8)]

    landpattern = DDR5ControllerBGALandpattern()
    symbol = BoxSymbol()


def _generate_ctrl_mapping():
    """Generate pad mapping for DDR5 controller (20x20 BGA)."""
    lp = DDR5ControllerComponent.landpattern
    pad_map = {}
    pad_idx = 0

    all_ports = []
    for dq in DDR5ControllerComponent.DQ:
        all_ports.append(dq)
    for dqs_p in DDR5ControllerComponent.DQS_P:
        all_ports.append(dqs_p)
    for dqs_n in DDR5ControllerComponent.DQS_N:
        all_ports.append(dqs_n)
    for dmi in DDR5ControllerComponent.DMI:
        all_ports.append(dmi)
    all_ports.append(DDR5ControllerComponent.CK_P)
    all_ports.append(DDR5ControllerComponent.CK_N)
    for ca in DDR5ControllerComponent.CA:
        all_ports.append(ca)
    all_ports.append(DDR5ControllerComponent.CS_N)
    all_ports.append(DDR5ControllerComponent.CKE)
    all_ports.append(DDR5ControllerComponent.ODT)
    all_ports.append(DDR5ControllerComponent.RESET_N)
    all_ports.append(DDR5ControllerComponent.ALERT_N)
    for vdd in DDR5ControllerComponent.VDD:
        all_ports.append(vdd)
    for vss in DDR5ControllerComponent.VSS:
        all_ports.append(vss)
    for vddq in DDR5ControllerComponent.VDDQ:
        all_ports.append(vddq)

    for row in range(20):
        row_letter = _ctrl_row_name(row)
        for col in range(20):
            col_num = col + 1
            if pad_idx < len(all_ports):
                pad_ref = getattr(lp, row_letter)[col_num]
                pad_map[all_ports[pad_idx]] = pad_ref
                pad_idx += 1

    return pad_map


DDR5ControllerComponent.mapping = [PadMapping(_generate_ctrl_mapping())]


# =============================================================================
# DDR5 Controller Circuit -- Provide pattern for pin assignment
# =============================================================================


class DDR5ControllerCircuit(Circuit):
    """DDR5 Controller Circuit

    Maps DDR5 bundle to controller component pins using Provide pattern.
    """

    pwr = Power()

    def __init__(self):
        self.ctrl = DDR5ControllerComponent()

        self.ddr5_provide = Provide(DDR5(DDR5Width.x16, DDR5Rank.SingleRank)).one_of(
            lambda b: [self._create_ddr5_mapping(b)]
        )

    def _create_ddr5_mapping(self, b: DDR5) -> dict:
        """Create mapping from DDR5 bundle signals to controller component pins."""
        mapping = {}

        # DQ mapping
        for i in range(16):
            mapping[b.data.DQ[i]] = self.ctrl.DQ[i]

        # DQS mapping
        mapping[b.data.DQS[0].p] = self.ctrl.DQS_P[0]
        mapping[b.data.DQS[0].n] = self.ctrl.DQS_N[0]
        mapping[b.data.DQS[1].p] = self.ctrl.DQS_P[1]
        mapping[b.data.DQS[1].n] = self.ctrl.DQS_N[1]

        # DMI mapping
        mapping[b.data.DMI[0]] = self.ctrl.DMI[0]
        mapping[b.data.DMI[1]] = self.ctrl.DMI[1]

        # CA mapping
        for i in range(14):
            mapping[b.ca.CA[i]] = self.ctrl.CA[i]

        # CK mapping
        mapping[b.ca.CK.p] = self.ctrl.CK_P
        mapping[b.ca.CK.n] = self.ctrl.CK_N

        # Control signals
        mapping[b.ca.CS_n[0]] = self.ctrl.CS_N
        mapping[b.ca.CKE[0]] = self.ctrl.CKE
        mapping[b.ca.ODT[0]] = self.ctrl.ODT
        mapping[b.ca.RESET_n] = self.ctrl.RESET_N
        mapping[b.ca.ALERT_n] = self.ctrl.ALERT_N

        return mapping
