"""DDR4 Example Components

Exact translation of components/MT40A1G16TB-062E-F.stanza to Python.

This provides a real Micron DDR4 memory component (MT40A1G16TB-062E-F) with
the exact FBGA96 split BGA landpattern and pin mappings.
"""

from collections.abc import Iterable

from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.net import Port, Provide
from jitx.shapes.primitive import Circle
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitxlib.landpatterns.courtyard import ExcessCourtyard
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.grid_layout import (
    A1,
    AlphaDictNumbering,
    GridLandpatternGenerator,
    GridPosition,
)
from jitxlib.landpatterns.grid_planner import GridPlannerMixin
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import GridPadShapeGeneratorMixin, SMDPadConfig
from jitxlib.landpatterns.silkscreen.marker import Pad1Marker
from jitxlib.landpatterns.silkscreen.outlines import SilkscreenOutline
from jitxlib.symbols.box import BoxSymbol

from ....protocols.memory.ddr4 import DDR4, DDR4Rank, DDR4Width


class SplitBGABase(
    GridPlannerMixin,
    GridPadShapeGeneratorMixin,
    GridLandpatternGenerator,
):
    """Split BGA Base Class for DDR4

    Creates a split BGA with two halves separated by a gap.
    Exact translation of FBGA96 build-pads method from MT40A1G16TB-062E-F.stanza.
    """

    def __init__(
        self,
        num_rows: int = 16,
        half_cols: int = 3,
        ball_diameter: float = 0.42,
        pitch: float = 0.80,
        gap: float = 3.20,
    ):
        super().__init__()
        self._num_rows = num_rows
        self._half_cols = half_cols
        self._num_cols = 9  # Total columns including gap
        self._pitch = pitch
        self._gap = gap
        self.pad_shape(Circle(diameter=ball_diameter))

    def _generate_layout(self) -> Iterable[GridPosition]:
        """Generate split BGA layout with two halves separated by gap.

        Exact translation of build-pads from MT40A1G16TB-062E-F.stanza:
        - val all-rows = 16
        - val part-cols = 3
        - val ex = 3.200
        - val l = (to-double(part-cols - 1) * x(pitch) + ex) / 2.0
        - first-offset  = Point(-1.0 * l, 0.00)
        - second-offset = Point( l, 0.00)
        """
        # Calculate offset as per Stanza: l = ((part_cols - 1) * pitch + gap) / 2
        half_offset = ((self._half_cols - 1) * self._pitch + self._gap) / 2.0

        center_row = (self._num_rows - 1) / 2.0
        half_center_col = (self._half_cols - 1) / 2.0

        for r in range(self._num_rows):
            row_y = (center_row - r) * self._pitch

            # First half (columns 0-2 in grid, map to 1-3 in naming)
            for c in range(self._half_cols):
                x = (c - half_center_col) * self._pitch - half_offset
                tx = Transform.translate(x, row_y)
                yield GridPosition(r, c, tx)

            # Second half (columns 6-8 in grid, map to 7-9 in naming)
            for c in range(self._half_cols):
                x = (c - half_center_col) * self._pitch + half_offset
                # Column index is c + 6 (to create columns 7, 8, 9)
                yield GridPosition(r, c + 6, Transform.translate(x, row_y))


class SplitBGADecorated(SilkscreenOutline, Pad1Marker, ExcessCourtyard, SplitBGABase):
    """Split BGA with decorations"""

    def __base_init__(self):
        super().__base_init__()


class DDR4NumberingScheme(AlphaDictNumbering):
    """Custom numbering scheme for DDR4 split BGA.

    Maps grid columns 0-2 to pad columns 1-3, and grid columns 6-8 to pad columns 7-9.
    """

    def col_name(self, col: int) -> str:
        """Convert column index to column number string."""
        # Columns 0-2 map to 1-3, columns 6-8 map to 7-9
        return str(col + 1)


class FBGA96(A1, DDR4NumberingScheme, SplitBGADecorated):
    """FBGA96 Split BGA Landpattern for DDR4 Memory Component

    Exact translation from components/MT40A1G16TB-062E-F.stanza:
    - 96-ball split BGA (16 rows x 9 columns in two 3-column halves)
    - Pitch: 0.80mm
    - Ball diameter: 0.42mm (solder mask defined pad)
    - Gap between halves: 3.2mm
    - Package body: 7.50mm x 13.0mm x 1.1mm
    - Density level C
    - Copper adjustment: +0.05mm (hack for solder mask defined pad)
    """

    def __init__(self):
        super().__init__(
            num_rows=16,
            half_cols=3,
            ball_diameter=0.42,
            pitch=0.80,
            gap=3.20,
        )
        # Note: Stanza uses copper-D-adj = 0.05 hack for solder mask defined pad
        self.pad_config(SMDPadConfig(copper=0.05))
        self.package_body(
            RectanglePackage(
                width=Toleranced(7.50, 0.0),
                length=Toleranced(13.0, 0.0),
                height=Toleranced(1.1, 0.0),
            )
        )
        self.density_level(DensityLevel.C)


class MT40A1G16TB_062E_F(Component):
    """Micron DDR4 SDRAM MT40A1G16TB-062E-F

    Exact translation from components/MT40A1G16TB-062E-F.stanza.
    16Gb DDR4 SDRAM with x16 interface in FBGA96 package.

    Pin structure:
    - DQ[16] - 16-bit data bus (split into upper/lower bytes)
    - A[17] - Address bus
    - BA[2] - Bank address
    - BG[1] - Bank group (x16 has only 1 bit)
    - CK_P/CK_N - Differential clock
    - CS_N, CKE, ODT, ACT_N, RESET_N, PAR, ALERT_N - Control
    - LDQS_P/N, UDQS_P/N - Lower/Upper data strobes
    - LDM_N, UDM_N - Lower/Upper data masks
    - VDD, VDDQ, VSS, VSSQ - Power/Ground
    - VPP, VREFCA, ZQ - Other
    """

    reference_prefix = "U"
    mpn = "MT40A1G16TB-062E:F"
    description = "Micron 16Gb DDR4 SDRAM"

    # Data signals (x16 = 16 DQ bits)
    DQ = [Port() for _ in range(16)]

    # Address (17 bits for DDR4)
    A = [Port() for _ in range(17)]

    # Bank address and bank group
    BA = [Port() for _ in range(2)]
    BG = [Port() for _ in range(1)]

    # Clock
    CK_P = Port()
    CK_N = Port()

    # Control signals
    CKE = Port()
    CS_N = Port()
    ODT = Port()
    ACT_N = Port()
    RESET_N = Port()
    PAR = Port()
    TEN = Port()
    ALERT_N = Port()
    NC = Port()

    # Data strobes (separate upper and lower)
    UDQS_P = Port()
    UDQS_N = Port()
    LDQS_P = Port()
    LDQS_N = Port()

    # Data masks
    UDM_N = Port()
    LDM_N = Port()

    # Power and ground
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(9)]
    VDDQ = [Port() for _ in range(10)]
    VSSQ = [Port() for _ in range(10)]

    # Other power/reference
    VPP = [Port() for _ in range(2)]
    VREFCA = Port()
    ZQ = Port()

    landpattern = FBGA96()
    symbol = BoxSymbol()

    # Exact pad mapping from MT40A1G16TB-062E-F.stanza pin-properties
    mapping = [
        PadMapping(
            {
                # Data bus - Lower byte (DQ0-DQ7)
                DQ[0]: landpattern.G[2],
                DQ[1]: landpattern.F[7],
                DQ[2]: landpattern.H[3],
                DQ[3]: landpattern.H[7],
                DQ[4]: landpattern.H[2],
                DQ[5]: landpattern.H[8],
                DQ[6]: landpattern.J[3],
                DQ[7]: landpattern.J[7],
                # Data bus - Upper byte (DQ8-DQ15)
                DQ[8]: landpattern.A[3],
                DQ[9]: landpattern.B[8],
                DQ[10]: landpattern.C[3],
                DQ[11]: landpattern.C[7],
                DQ[12]: landpattern.C[2],
                DQ[13]: landpattern.C[8],
                DQ[14]: landpattern.D[3],
                DQ[15]: landpattern.D[7],
                # Address bus
                A[0]: landpattern.P[3],
                A[1]: landpattern.P[7],
                A[2]: landpattern.R[3],
                A[3]: landpattern.N[7],
                A[4]: landpattern.N[3],
                A[5]: landpattern.P[8],
                A[6]: landpattern.P[2],
                A[7]: landpattern.R[8],
                A[8]: landpattern.R[2],
                A[9]: landpattern.R[7],
                A[10]: landpattern.M[3],  # A10/AP
                A[11]: landpattern.T[2],
                A[12]: landpattern.M[7],  # A12/BC_n
                A[13]: landpattern.T[8],
                A[14]: landpattern.L[2],  # A14/WE_n
                A[15]: landpattern.M[8],  # A15/CAS_n
                A[16]: landpattern.L[8],  # A16/RAS_n
                # Bank address and group
                BA[0]: landpattern.N[2],
                BA[1]: landpattern.N[8],
                BG[0]: landpattern.M[2],
                # Clock
                CK_P: landpattern.K[7],
                CK_N: landpattern.K[8],
                # Control signals
                CKE: landpattern.K[2],
                CS_N: landpattern.L[7],
                ODT: landpattern.K[3],
                ACT_N: landpattern.L[3],
                RESET_N: landpattern.P[1],
                PAR: landpattern.T[3],
                TEN: landpattern.N[9],
                ALERT_N: landpattern.P[9],
                NC: landpattern.T[7],
                # Data strobes
                UDQS_P: landpattern.B[7],
                UDQS_N: landpattern.A[7],
                LDQS_P: landpattern.G[3],
                LDQS_N: landpattern.F[3],
                # Data masks
                UDM_N: landpattern.E[2],
                LDM_N: landpattern.E[7],
                # VDD
                VDD[0]: landpattern.B[3],
                VDD[1]: landpattern.B[9],
                VDD[2]: landpattern.D[1],
                VDD[3]: landpattern.G[7],
                VDD[4]: landpattern.J[1],
                VDD[5]: landpattern.J[9],
                VDD[6]: landpattern.L[1],
                VDD[7]: landpattern.L[9],
                VDD[8]: landpattern.R[1],
                VDD[9]: landpattern.T[9],
                # VSS
                VSS[0]: landpattern.B[2],
                VSS[1]: landpattern.E[1],
                VSS[2]: landpattern.E[9],
                VSS[3]: landpattern.G[8],
                VSS[4]: landpattern.K[1],
                VSS[5]: landpattern.K[9],
                VSS[6]: landpattern.M[9],
                VSS[7]: landpattern.N[1],
                VSS[8]: landpattern.T[1],
                # VDDQ
                VDDQ[0]: landpattern.A[1],
                VDDQ[1]: landpattern.A[9],
                VDDQ[2]: landpattern.C[1],
                VDDQ[3]: landpattern.D[9],
                VDDQ[4]: landpattern.F[2],
                VDDQ[5]: landpattern.F[8],
                VDDQ[6]: landpattern.G[1],
                VDDQ[7]: landpattern.G[9],
                VDDQ[8]: landpattern.J[2],
                VDDQ[9]: landpattern.J[8],
                # VSSQ
                VSSQ[0]: landpattern.A[2],
                VSSQ[1]: landpattern.A[8],
                VSSQ[2]: landpattern.C[9],
                VSSQ[3]: landpattern.D[2],
                VSSQ[4]: landpattern.D[8],
                VSSQ[5]: landpattern.E[3],
                VSSQ[6]: landpattern.E[8],
                VSSQ[7]: landpattern.F[1],
                VSSQ[8]: landpattern.H[1],
                VSSQ[9]: landpattern.H[9],
                # Other power/reference
                VPP[0]: landpattern.B[1],
                VPP[1]: landpattern.R[9],
                VREFCA: landpattern.M[1],
                ZQ: landpattern.F[9],
            }
        )
    ]


class DDR4MemoryCircuit(Circuit):
    """DDR4 Memory Circuit

    Maps DDR4 bundle to dual MT40A1G16TB-062E-F memory components.
    Uses 2 memory chips in fly-by topology where data and most control signals
    are shared across both chips.

    DDR4 Fly-by topology:
    - Shared signals (fan out to both chips): DQ, DQS, DM_n, A, BA, ACT_n, RESET_n, PAR, ALERT_n
    - Per-chip signals: CK, CS_n, CKE, ODT, BG
    """

    # DDR4 interface port - directly connected to memories
    io = DDR4(DDR4Width.x16, DDR4Rank.SingleRank)
    pwr = Power()
    pwr_q = Power()
    VPP = Port()
    VREFCA = Port()

    def __init__(self):
        # Instantiate 2 memory chips for fly-by topology
        self.mem0 = MT40A1G16TB_062E_F()
        self.mem1 = MT40A1G16TB_062E_F()

        # Power connections for both chips
        pwr_net = self.pwr.Vp
        for vdd in self.mem0.VDD:
            pwr_net = pwr_net + vdd
        for vdd in self.mem1.VDD:
            pwr_net = pwr_net + vdd
        self.vdd_net = pwr_net

        gnd_net = self.pwr.Vn
        for vss in self.mem0.VSS:
            gnd_net = gnd_net + vss
        for vss in self.mem1.VSS:
            gnd_net = gnd_net + vss
        self.vss_net = gnd_net

        vddq_net = self.pwr_q.Vp
        for vddq in self.mem0.VDDQ:
            vddq_net = vddq_net + vddq
        for vddq in self.mem1.VDDQ:
            vddq_net = vddq_net + vddq
        self.vddq_net = vddq_net

        vssq_net = self.pwr_q.Vn
        for vssq in self.mem0.VSSQ:
            vssq_net = vssq_net + vssq
        for vssq in self.mem1.VSSQ:
            vssq_net = vssq_net + vssq
        self.vssq_net = vssq_net

        vpp_net = self.VPP
        for vpp in self.mem0.VPP:
            vpp_net = vpp_net + vpp
        for vpp in self.mem1.VPP:
            vpp_net = vpp_net + vpp
        self.vpp_net = vpp_net

        self.vrefca_net = self.VREFCA + self.mem0.VREFCA + self.mem1.VREFCA

        # ============================================================
        # DDR4 Fly-by topology connections
        # Connect io bundle directly to both memory chips
        # Use >> for topology preservation, then chain to second chip
        # ============================================================

        topos = []

        # DQ - shared, fan out to both memories (fly-by topology)
        for i in range(16):
            topos.append(self.io.data.DQ[i] >> self.mem0.DQ[i])
            topos.append(self.mem0.DQ[i] >> self.mem1.DQ[i])

        # DQS - shared differential pairs, fan out to both memories
        # Lower byte DQS
        topos.append(self.io.data.DQS[0].p >> self.mem0.LDQS_P)
        topos.append(self.mem0.LDQS_P >> self.mem1.LDQS_P)
        topos.append(self.io.data.DQS[0].n >> self.mem0.LDQS_N)
        topos.append(self.mem0.LDQS_N >> self.mem1.LDQS_N)

        # Upper byte DQS
        topos.append(self.io.data.DQS[1].p >> self.mem0.UDQS_P)
        topos.append(self.mem0.UDQS_P >> self.mem1.UDQS_P)
        topos.append(self.io.data.DQS[1].n >> self.mem0.UDQS_N)
        topos.append(self.mem0.UDQS_N >> self.mem1.UDQS_N)

        # DM_n - shared, fan out to both memories
        topos.append(self.io.data.DM_n[0] >> self.mem0.LDM_N)
        topos.append(self.mem0.LDM_N >> self.mem1.LDM_N)
        topos.append(self.io.data.DM_n[1] >> self.mem0.UDM_N)
        topos.append(self.mem0.UDM_N >> self.mem1.UDM_N)

        # Address - shared, fan out to both memories
        for i in range(17):
            topos.append(self.io.acc.A[i] >> self.mem0.A[i])
            topos.append(self.mem0.A[i] >> self.mem1.A[i])

        # Bank address - shared, fan out to both memories
        for i in range(2):
            topos.append(self.io.acc.BA[i] >> self.mem0.BA[i])
            topos.append(self.mem0.BA[i] >> self.mem1.BA[i])

        # Bank group - per-chip (x16 only has 1 BG per chip)
        topos.append(self.io.acc.BG[0] >> self.mem0.BG[0])
        topos.append(self.io.acc.BG[1] >> self.mem1.BG[0])

        # CK - per-chip differential pairs
        topos.append(self.io.acc.CK[0].p >> self.mem0.CK_P)
        topos.append(self.io.acc.CK[0].n >> self.mem0.CK_N)
        topos.append(self.io.acc.CK[1].p >> self.mem1.CK_P)
        topos.append(self.io.acc.CK[1].n >> self.mem1.CK_N)

        # Control signals - per-chip
        topos.append(self.io.acc.CKE[0] >> self.mem0.CKE)
        topos.append(self.io.acc.CS_n[0] >> self.mem0.CS_N)
        topos.append(self.io.acc.ODT[0] >> self.mem0.ODT)

        # Second chip control signals (if bundle supports dual rank)
        if len(self.io.acc.CKE) > 1:
            topos.append(self.io.acc.CKE[1] >> self.mem1.CKE)
        if len(self.io.acc.CS_n) > 1:
            topos.append(self.io.acc.CS_n[1] >> self.mem1.CS_N)
        if len(self.io.acc.ODT) > 1:
            topos.append(self.io.acc.ODT[1] >> self.mem1.ODT)

        # Shared control signals - fan out to both memories
        topos.append(self.io.acc.ACT_n >> self.mem0.ACT_N)
        topos.append(self.mem0.ACT_N >> self.mem1.ACT_N)
        topos.append(self.io.acc.RESET_n >> self.mem0.RESET_N)
        topos.append(self.mem0.RESET_N >> self.mem1.RESET_N)
        topos.append(self.io.acc.PAR >> self.mem0.PAR)
        topos.append(self.mem0.PAR >> self.mem1.PAR)
        topos.append(self.io.acc.ALERT_n >> self.mem0.ALERT_N)
        topos.append(self.mem0.ALERT_N >> self.mem1.ALERT_N)

        self.topos = topos


# Alias for backward compatibility
DDR4MemoryComponent = MT40A1G16TB_062E_F


class DDR4ControllerBGALandpattern(BGA):
    """BGA Landpattern for DDR4 Controller Component

    Standard BGA for controller/SoC side.
    """

    def __init__(self):
        super().__init__(
            num_rows=20,
            num_cols=20,
            ball_diameter=0.40,
            pitch=0.65,
        )
        self.pad_config(SMDPadConfig())
        self.density_level(DensityLevel.B)


class DDR4ControllerComponent(Component):
    """DDR4 Controller Component

    Controller/SoC component with DDR4 interface pins.
    """

    reference_prefix = "U"
    mpn = "JITX-DDR4-CTRL"
    description = "Dummy DDR4 controller"

    # Same signal interface as memory
    DQ = [Port() for _ in range(16)]
    DQS_P = [Port() for _ in range(2)]
    DQS_N = [Port() for _ in range(2)]
    DM_N = [Port() for _ in range(2)]
    CK_P = Port()
    CK_N = Port()
    A = [Port() for _ in range(17)]
    BA = [Port() for _ in range(2)]
    BG = [Port() for _ in range(1)]
    CKE = Port()
    CS_N = Port()
    ODT = Port()
    ACT_N = Port()
    RESET_N = Port()
    PAR = Port()
    ALERT_N = Port()
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(40)]
    VDDQ = [Port() for _ in range(8)]

    landpattern = DDR4ControllerBGALandpattern()
    symbol = BoxSymbol()


# Reduced alphabet for BGA row naming (no I, O, Q, S, X, Z per JEDEC)
_CTRL_REDUCED_ALPHA = "ABCDEFGHJKLMNPRTUVWY"


def _ctrl_row_name(idx: int) -> str:
    """Convert row index to BGA row name using JEDEC reduced alphabet."""
    if idx < len(_CTRL_REDUCED_ALPHA):
        return _CTRL_REDUCED_ALPHA[idx]
    first = idx // len(_CTRL_REDUCED_ALPHA) - 1
    second = idx % len(_CTRL_REDUCED_ALPHA)
    return _CTRL_REDUCED_ALPHA[first] + _CTRL_REDUCED_ALPHA[second]


def _generate_ctrl_mapping():
    """Generate pad mapping for DDR4 controller (20x20 BGA)."""
    lp = DDR4ControllerComponent.landpattern
    pad_map = {}
    pad_idx = 0

    # Map all signal pins to pads
    all_ports = []

    # Collect all ports to map
    for dq in DDR4ControllerComponent.DQ:
        all_ports.append(dq)
    for dqs_p in DDR4ControllerComponent.DQS_P:
        all_ports.append(dqs_p)
    for dqs_n in DDR4ControllerComponent.DQS_N:
        all_ports.append(dqs_n)
    for dm_n in DDR4ControllerComponent.DM_N:
        all_ports.append(dm_n)
    all_ports.append(DDR4ControllerComponent.CK_P)
    all_ports.append(DDR4ControllerComponent.CK_N)
    for a in DDR4ControllerComponent.A:
        all_ports.append(a)
    for ba in DDR4ControllerComponent.BA:
        all_ports.append(ba)
    for bg in DDR4ControllerComponent.BG:
        all_ports.append(bg)
    all_ports.append(DDR4ControllerComponent.CKE)
    all_ports.append(DDR4ControllerComponent.CS_N)
    all_ports.append(DDR4ControllerComponent.ODT)
    all_ports.append(DDR4ControllerComponent.ACT_N)
    all_ports.append(DDR4ControllerComponent.RESET_N)
    all_ports.append(DDR4ControllerComponent.PAR)
    all_ports.append(DDR4ControllerComponent.ALERT_N)
    for vdd in DDR4ControllerComponent.VDD:
        all_ports.append(vdd)
    for vss in DDR4ControllerComponent.VSS:
        all_ports.append(vss)
    for vddq in DDR4ControllerComponent.VDDQ:
        all_ports.append(vddq)

    # Map ports to pads sequentially
    for row in range(20):
        row_letter = _ctrl_row_name(row)
        for col in range(20):
            col_num = col + 1
            if pad_idx < len(all_ports):
                pad_ref = getattr(lp, row_letter)[col_num]
                pad_map[all_ports[pad_idx]] = pad_ref
                pad_idx += 1

    return pad_map


# Build the controller mapping after class definition
DDR4ControllerComponent.mapping = [PadMapping(_generate_ctrl_mapping())]


class DDR4ControllerComponent2(Component):
    """DDR4 Controller Component with full signal set

    Controller/SoC component with DDR4 interface pins supporting 2 BG and 2 CK.
    """

    reference_prefix = "U"
    mpn = "JITX-DDR4-CTRL2"
    description = "Dummy DDR4 controller with dual rank support"

    # Data signals
    DQ = [Port() for _ in range(16)]
    DQS_P = [Port() for _ in range(2)]
    DQS_N = [Port() for _ in range(2)]
    DM_N = [Port() for _ in range(2)]

    # Clock - 2 pairs for dual rank
    CK_P = [Port() for _ in range(2)]
    CK_N = [Port() for _ in range(2)]

    # Address and bank
    A = [Port() for _ in range(17)]
    BA = [Port() for _ in range(2)]
    BG = [Port() for _ in range(2)]  # 2 BG signals

    # Control signals - 2 each for dual rank
    CKE = [Port() for _ in range(2)]
    CS_N = [Port() for _ in range(2)]
    ODT = [Port() for _ in range(2)]
    ACT_N = Port()
    RESET_N = Port()
    PAR = Port()
    ALERT_N = Port()

    # Power
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(40)]
    VDDQ = [Port() for _ in range(8)]

    landpattern = DDR4ControllerBGALandpattern()
    symbol = BoxSymbol()


def _generate_ctrl2_mapping():
    """Generate pad mapping for DDR4 controller 2 (20x20 BGA)."""
    lp = DDR4ControllerComponent2.landpattern
    pad_map = {}
    pad_idx = 0

    # Collect all ports to map
    all_ports = []
    for dq in DDR4ControllerComponent2.DQ:
        all_ports.append(dq)
    for dqs_p in DDR4ControllerComponent2.DQS_P:
        all_ports.append(dqs_p)
    for dqs_n in DDR4ControllerComponent2.DQS_N:
        all_ports.append(dqs_n)
    for dm_n in DDR4ControllerComponent2.DM_N:
        all_ports.append(dm_n)
    for ck_p in DDR4ControllerComponent2.CK_P:
        all_ports.append(ck_p)
    for ck_n in DDR4ControllerComponent2.CK_N:
        all_ports.append(ck_n)
    for a in DDR4ControllerComponent2.A:
        all_ports.append(a)
    for ba in DDR4ControllerComponent2.BA:
        all_ports.append(ba)
    for bg in DDR4ControllerComponent2.BG:
        all_ports.append(bg)
    for cke in DDR4ControllerComponent2.CKE:
        all_ports.append(cke)
    for cs_n in DDR4ControllerComponent2.CS_N:
        all_ports.append(cs_n)
    for odt in DDR4ControllerComponent2.ODT:
        all_ports.append(odt)
    all_ports.append(DDR4ControllerComponent2.ACT_N)
    all_ports.append(DDR4ControllerComponent2.RESET_N)
    all_ports.append(DDR4ControllerComponent2.PAR)
    all_ports.append(DDR4ControllerComponent2.ALERT_N)
    for vdd in DDR4ControllerComponent2.VDD:
        all_ports.append(vdd)
    for vss in DDR4ControllerComponent2.VSS:
        all_ports.append(vss)
    for vddq in DDR4ControllerComponent2.VDDQ:
        all_ports.append(vddq)

    # Map ports to pads sequentially
    for row in range(20):
        row_letter = _ctrl_row_name(row)
        for col in range(20):
            col_num = col + 1
            if pad_idx < len(all_ports):
                pad_ref = getattr(lp, row_letter)[col_num]
                pad_map[all_ports[pad_idx]] = pad_ref
                pad_idx += 1

    return pad_map


DDR4ControllerComponent2.mapping = [PadMapping(_generate_ctrl2_mapping())]


class DDR4ControllerCircuit(Circuit):
    """DDR4 Controller Circuit

    Maps DDR4 bundle to controller component pins with full signal support.
    Uses Provide pattern for proper connectivity (equivalent to Stanza's supports).
    """

    pwr = Power()

    def __init__(self):
        self.ctrl = DDR4ControllerComponent2()

        # Provide a DDR4 interface with default parameters (2 CK, 2 BG)
        self.ddr4_provide = Provide(DDR4(DDR4Width.x16, DDR4Rank.SingleRank)).one_of(
            lambda b: [self._create_ddr4_mapping(b)]
        )

    def _create_ddr4_mapping(self, b: DDR4) -> dict:
        """Create mapping from DDR4 bundle signals to controller component pins."""
        mapping = {}

        # DQ mapping
        for i in range(16):
            mapping[b.data.DQ[i]] = self.ctrl.DQ[i]

        # DQS mapping
        mapping[b.data.DQS[0].p] = self.ctrl.DQS_P[0]
        mapping[b.data.DQS[0].n] = self.ctrl.DQS_N[0]
        mapping[b.data.DQS[1].p] = self.ctrl.DQS_P[1]
        mapping[b.data.DQS[1].n] = self.ctrl.DQS_N[1]

        # DM_n mapping
        mapping[b.data.DM_n[0]] = self.ctrl.DM_N[0]
        mapping[b.data.DM_n[1]] = self.ctrl.DM_N[1]

        # Address mapping
        for i in range(17):
            mapping[b.acc.A[i]] = self.ctrl.A[i]

        # Bank address mapping
        for i in range(2):
            mapping[b.acc.BA[i]] = self.ctrl.BA[i]

        # Bank group - 2 BG signals
        mapping[b.acc.BG[0]] = self.ctrl.BG[0]
        mapping[b.acc.BG[1]] = self.ctrl.BG[1]

        # Clock - 2 CK pairs
        mapping[b.acc.CK[0].p] = self.ctrl.CK_P[0]
        mapping[b.acc.CK[0].n] = self.ctrl.CK_N[0]
        mapping[b.acc.CK[1].p] = self.ctrl.CK_P[1]
        mapping[b.acc.CK[1].n] = self.ctrl.CK_N[1]

        # Control signals - 2 each for dual rank support
        mapping[b.acc.CKE[0]] = self.ctrl.CKE[0]
        mapping[b.acc.CS_n[0]] = self.ctrl.CS_N[0]
        mapping[b.acc.ODT[0]] = self.ctrl.ODT[0]

        if len(b.acc.CKE) > 1:
            mapping[b.acc.CKE[1]] = self.ctrl.CKE[1]
        if len(b.acc.CS_n) > 1:
            mapping[b.acc.CS_n[1]] = self.ctrl.CS_N[1]
        if len(b.acc.ODT) > 1:
            mapping[b.acc.ODT[1]] = self.ctrl.ODT[1]

        # Shared control signals
        mapping[b.acc.ACT_n] = self.ctrl.ACT_N
        mapping[b.acc.RESET_n] = self.ctrl.RESET_N
        mapping[b.acc.PAR] = self.ctrl.PAR
        mapping[b.acc.ALERT_n] = self.ctrl.ALERT_N

        return mapping
