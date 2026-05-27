"""Micron MT40A1G16TB-062E-F DDR4 SDRAM Component

16Gb DDR4 SDRAM with x16 interface in FBGA96 split BGA package.
Exact translation of components/MT40A1G16TB-062E-F.stanza to Python.

Also provides DDR4SingleMemoryCircuit — a single-chip wrapper with a fixed
DDR4 bundle port and proper per-rail power wiring.
"""

from collections.abc import Iterable

from jitx import Net, PadMapping
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.net import Port
from jitx.shapes.primitive import Circle
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitxlib.landpatterns.courtyard import ExcessCourtyard
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

from jitx_protocols_ext.protocols.memory.ddr4 import DDR4, DDR4Rank, DDR4Width

# =============================================================================
# Landpattern
# =============================================================================


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
        self._num_cols = 9
        self._pitch = pitch
        self._gap = gap
        self.pad_shape(Circle(diameter=ball_diameter))

    def _generate_layout(self) -> Iterable[GridPosition]:
        half_offset = ((self._half_cols - 1) * self._pitch + self._gap) / 2.0
        center_row = (self._num_rows - 1) / 2.0
        half_center_col = (self._half_cols - 1) / 2.0

        for r in range(self._num_rows):
            row_y = (center_row - r) * self._pitch

            for c in range(self._half_cols):
                x = (c - half_center_col) * self._pitch - half_offset
                tx = Transform.translate(x, row_y)
                yield GridPosition(r, c, tx)

            for c in range(self._half_cols):
                x = (c - half_center_col) * self._pitch + half_offset
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
        return str(col + 1)


class FBGA96(A1, DDR4NumberingScheme, SplitBGADecorated):
    """FBGA96 Split BGA Landpattern for DDR4 Memory Component

    96-ball split BGA (16 rows x 9 columns in two 3-column halves)
    - Pitch: 0.80mm, Ball diameter: 0.42mm
    - Gap between halves: 3.2mm
    - Package body: 7.50mm x 13.0mm x 1.1mm
    - Density level C
    """

    def __init__(self):
        super().__init__(
            num_rows=16,
            half_cols=3,
            ball_diameter=0.42,
            pitch=0.80,
            gap=3.20,
        )
        self.pad_config(SMDPadConfig(copper=0.05))
        self.package_body(
            RectanglePackage(
                width=Toleranced(7.50, 0.0),
                length=Toleranced(13.0, 0.0),
                height=Toleranced(1.1, 0.0),
            )
        )
        self.density_level(DensityLevel.C)


# =============================================================================
# Component
# =============================================================================


class MT40A1G16TB_062E_F(Component):
    """Micron DDR4 SDRAM MT40A1G16TB-062E-F

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

    DQ = [Port() for _ in range(16)]
    A = [Port() for _ in range(17)]
    BA = [Port() for _ in range(2)]
    BG = [Port() for _ in range(1)]
    CK_P = Port()
    CK_N = Port()
    CKE = Port()
    CS_N = Port()
    ODT = Port()
    ACT_N = Port()
    RESET_N = Port()
    PAR = Port()
    TEN = Port()
    ALERT_N = Port()
    NC = Port()
    UDQS_P = Port()
    UDQS_N = Port()
    LDQS_P = Port()
    LDQS_N = Port()
    UDM_N = Port()
    LDM_N = Port()
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(9)]
    VDDQ = [Port() for _ in range(10)]
    VSSQ = [Port() for _ in range(10)]
    VPP = [Port() for _ in range(2)]
    VREFCA = Port()
    ZQ = Port()

    landpattern = FBGA96()
    symbol = BoxSymbol()

    mapping = [
        PadMapping(
            {
                DQ[0]: landpattern.G[2],
                DQ[1]: landpattern.F[7],
                DQ[2]: landpattern.H[3],
                DQ[3]: landpattern.H[7],
                DQ[4]: landpattern.H[2],
                DQ[5]: landpattern.H[8],
                DQ[6]: landpattern.J[3],
                DQ[7]: landpattern.J[7],
                DQ[8]: landpattern.A[3],
                DQ[9]: landpattern.B[8],
                DQ[10]: landpattern.C[3],
                DQ[11]: landpattern.C[7],
                DQ[12]: landpattern.C[2],
                DQ[13]: landpattern.C[8],
                DQ[14]: landpattern.D[3],
                DQ[15]: landpattern.D[7],
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
                A[10]: landpattern.M[3],
                A[11]: landpattern.T[2],
                A[12]: landpattern.M[7],
                A[13]: landpattern.T[8],
                A[14]: landpattern.L[2],
                A[15]: landpattern.M[8],
                A[16]: landpattern.L[8],
                BA[0]: landpattern.N[2],
                BA[1]: landpattern.N[8],
                BG[0]: landpattern.M[2],
                CK_P: landpattern.K[7],
                CK_N: landpattern.K[8],
                CKE: landpattern.K[2],
                CS_N: landpattern.L[7],
                ODT: landpattern.K[3],
                ACT_N: landpattern.L[3],
                RESET_N: landpattern.P[1],
                PAR: landpattern.T[3],
                TEN: landpattern.N[9],
                ALERT_N: landpattern.P[9],
                NC: landpattern.T[7],
                UDQS_P: landpattern.B[7],
                UDQS_N: landpattern.A[7],
                LDQS_P: landpattern.G[3],
                LDQS_N: landpattern.F[3],
                UDM_N: landpattern.E[2],
                LDM_N: landpattern.E[7],
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
                VSS[0]: landpattern.B[2],
                VSS[1]: landpattern.E[1],
                VSS[2]: landpattern.E[9],
                VSS[3]: landpattern.G[8],
                VSS[4]: landpattern.K[1],
                VSS[5]: landpattern.K[9],
                VSS[6]: landpattern.M[9],
                VSS[7]: landpattern.N[1],
                VSS[8]: landpattern.T[1],
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
                VPP[0]: landpattern.B[1],
                VPP[1]: landpattern.R[9],
                VREFCA: landpattern.M[1],
                ZQ: landpattern.F[9],
            }
        )
    ]


# =============================================================================
# Single-chip DDR4 Memory Circuit
# =============================================================================


class DDR4SingleMemoryCircuit(Circuit):
    """DDR4 Single Memory Circuit

    Wraps a single MT40A1G16TB-062E-F with a fixed DDR4 bundle port (io)
    and proper per-rail power wiring. Uses x16 SingleRank with 1 CK pair,
    1 BG, and 1 each of CKE/CS_n/ODT.
    """

    io = DDR4(DDR4Width.x16, DDR4Rank.SingleRank, ck_count=1, bg_count=1)
    pwr_vdd = Power()
    pwr_vddq = Power()
    pwr_vpp = Power()
    vrefca = Port()
    zq = Port()

    def __init__(self):
        self.mem = MT40A1G16TB_062E_F()

        # Power rail wiring
        self.vss_net = Net([self.pwr_vdd.Vn, self.pwr_vpp.Vn, *self.mem.VSS], name="VSS")
        self.vdd_net = Net([self.pwr_vdd.Vp, *self.mem.VDD], name="VDD")
        self.vssq_net = Net([self.pwr_vddq.Vn, *self.mem.VSSQ], name="VSSQ")
        self.vddq_net = Net([self.pwr_vddq.Vp, *self.mem.VDDQ], name="VDDQ")
        self.vpp_net = Net([self.pwr_vpp.Vp, *self.mem.VPP], name="VPP")

        # Fixed ports not in DDR4 bundle
        self.vrefca_net = self.vrefca + self.mem.VREFCA
        self.zq_net = self.zq + self.mem.ZQ

        # DDR4 signal topology: io bundle >> component pins
        topos = []

        # DQ
        for i in range(16):
            topos.append(self.io.data.DQ[i] >> self.mem.DQ[i])

        # DQS
        topos.append(self.io.data.DQS[0].p >> self.mem.LDQS_P)
        topos.append(self.io.data.DQS[0].n >> self.mem.LDQS_N)
        topos.append(self.io.data.DQS[1].p >> self.mem.UDQS_P)
        topos.append(self.io.data.DQS[1].n >> self.mem.UDQS_N)

        # DM_n
        topos.append(self.io.data.DM_n[0] >> self.mem.LDM_N)
        topos.append(self.io.data.DM_n[1] >> self.mem.UDM_N)

        # Address
        for i in range(17):
            topos.append(self.io.acc.A[i] >> self.mem.A[i])
        for i in range(2):
            topos.append(self.io.acc.BA[i] >> self.mem.BA[i])

        # BG (single chip has 1 BG)
        topos.append(self.io.acc.BG[0] >> self.mem.BG[0])

        # CK (single pair)
        topos.append(self.io.acc.CK[0].p >> self.mem.CK_P)
        topos.append(self.io.acc.CK[0].n >> self.mem.CK_N)

        # Control (single rank)
        topos.append(self.io.acc.CKE[0] >> self.mem.CKE)
        topos.append(self.io.acc.CS_n[0] >> self.mem.CS_N)
        topos.append(self.io.acc.ODT[0] >> self.mem.ODT)

        # Shared control
        topos.append(self.io.acc.ACT_n >> self.mem.ACT_N)
        topos.append(self.io.acc.RESET_n >> self.mem.RESET_N)
        topos.append(self.io.acc.PAR >> self.mem.PAR)
        topos.append(self.io.acc.ALERT_n >> self.mem.ALERT_N)

        self.topos = topos
