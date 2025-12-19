"""GDDR7 Example Components

Exact translation of jsl/examples/protocols/memory/gddr7/gddr7-src.stanza to Python.

This provides GDDR7 memory and GPU/IC components with full pin mappings
that exactly match the industry standard GDDR7 specification.
"""

from collections.abc import Iterable

from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.component import Component
from jitx.common import Power
from jitx.net import Port, Provide
from jitx.shapes.primitive import Circle
from jitx.toleranced import Toleranced
from jitx.transform import Transform

from jitxlib.landpatterns import LandpatternGenerator
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

from ....protocols.memory.gddr7 import GDDR7


class SplitBGABase(
    GridPlannerMixin,
    GridPadShapeGeneratorMixin,
    GridLandpatternGenerator,
):
    """Split BGA Base Class

    Creates a split BGA with two halves separated by a gap.
    Exact translation of FBGA266 build-pads method from gddr7-src.stanza.
    """

    def __init__(
        self,
        num_rows: int = 19,
        half_cols: int = 7,
        ball_diameter: float = 0.25,
        h_pitch: float = 0.75,
        v_pitch: float = 0.73,
        gap: float = 2.0,
    ):
        super().__init__()
        self._num_rows = num_rows
        self._half_cols = half_cols
        self._num_cols = half_cols * 2  # Total columns (14)
        self._h_pitch = h_pitch
        self._v_pitch = v_pitch
        self._gap = gap
        self.pad_shape(Circle(diameter=ball_diameter))

    def _generate_layout(self) -> Iterable[GridPosition]:
        """Generate split BGA layout with two halves separated by gap.

        Exact translation of build-pads from gddr7-src.stanza:
        - val all-rows = 19
        - val half-cols = 7
        - val ex = 2.000
        - val l = (to-double(half-cols - 1) * x(pitch) + ex) / 2.0
        - first-offset  = Point(-1.0 * l, 0.00)
        - second-offset = Point( l, 0.00)
        """
        # Calculate offset as per Stanza: l = ((half_cols - 1) * h_pitch + gap) / 2
        l = ((self._half_cols - 1) * self._h_pitch + self._gap) / 2.0

        center_row = (self._num_rows - 1) / 2.0
        half_center_col = (self._half_cols - 1) / 2.0

        for r in range(self._num_rows):
            row_y = (center_row - r) * self._v_pitch

            # First half (columns 0-6) - offset by -l
            for c in range(self._half_cols):
                x = (c - half_center_col) * self._h_pitch - l
                tx = Transform.translate(x, row_y)
                yield GridPosition(r, c, tx)

            # Second half (columns 7-13) - offset by +l
            for c in range(self._half_cols):
                x = (c - half_center_col) * self._h_pitch + l
                # Column index is c + half_cols (7-13)
                yield GridPosition(r, c + self._half_cols, tx := Transform.translate(x, row_y))


class SplitBGADecorated(SilkscreenOutline, Pad1Marker, ExcessCourtyard, SplitBGABase):
    """Split BGA with decorations"""

    def __base_init__(self):
        super().__base_init__()


class FBGA266(A1, AlphaDictNumbering, SplitBGADecorated):
    """FBGA266 Split BGA Landpattern for GDDR7 Memory Component

    Exact translation from jsl/examples/protocols/memory/gddr7/gddr7-src.stanza:
    - 266-ball split BGA (19 rows x 14 columns in two 7-column halves)
    - Non-uniform pitch: 0.75mm (x) x 0.73mm (y)
    - Ball diameter: 0.25mm
    - Gap between halves: 2.0mm
    - Package body: 12.0mm x 14.0mm x 1.0mm
    - Density level C
    - Copper adjustment: -0.05mm
    """

    def __init__(self):
        super().__init__(
            num_rows=19,
            half_cols=7,
            ball_diameter=0.25,
            h_pitch=0.75,
            v_pitch=0.73,
            gap=2.0,
        )
        self.pad_config(SMDPadConfig(copper=-0.05))
        self.package_body(
            RectanglePackage(
                width=Toleranced(12.0, 0.0),
                length=Toleranced(14.0, 0.0),
                height=Toleranced(1.0, 0.0),
            )
        )
        self.density_level(DensityLevel.C)


class GDDR7MemoryComponent(Component):
    """GDDR7 Memory Component

    Exact translation of mem-component from jsl/examples/protocols/memory/gddr7/gddr7-src.stanza.
    FBGA266 package with GDDR7 interface (4 data channels).

    Pin mapping follows JEDEC GDDR7 standard.
    """

    reference_prefix = "U"
    mpn = "memory-JITX-GDDR7"
    description = "Dummy GDDR7 memory"

    # DQ signals [10 bits][4 channels] - exact from Stanza: port DQp : pin[10][4]
    DQp = [[Port() for _ in range(4)] for _ in range(10)]

    # DQE (error detection) [4 channels] - exact from Stanza: port DQE : pin[4]
    DQE = [Port() for _ in range(4)]

    # CA signals [5 bits][4 channels] - exact from Stanza: port CA : pin[5][4]
    CA = [[Port() for _ in range(4)] for _ in range(5)]

    # Clock signals [4 channels]
    RCK_t = [Port() for _ in range(4)]
    RCK_c = [Port() for _ in range(4)]
    WCK_t = [Port() for _ in range(4)]
    WCK_c = [Port() for _ in range(4)]

    # ERR [4 channels] - exact from Stanza: port ERR : pin[4]
    ERR = [Port() for _ in range(4)]

    # Control signals
    RESET_n = Port()
    ZQ_AB = Port()
    ZQ_CD = Port()

    # Power pins - exact counts from Stanza (VSS[001]-VSS[125] = 125 pins)
    VSS = [Port() for _ in range(125)]
    VDD = [Port() for _ in range(22)]
    VDDQ = [Port() for _ in range(28)]
    VPP = [Port() for _ in range(4)]

    landpattern = FBGA266()
    symbol = BoxSymbol()

    # Exact pad mapping from Stanza JSL gddr7-src.stanza mem-component
    mapping = [
        PadMapping(
            {
                # Row A
                VSS[0]: landpattern.A[1],
                VSS[1]: landpattern.A[2],
                DQp[1][0]: landpattern.A[3],
                VSS[2]: landpattern.A[4],
                DQE[0]: landpattern.A[5],
                VSS[3]: landpattern.A[6],
                DQp[0][0]: landpattern.A[7],
                DQp[0][1]: landpattern.A[8],
                VSS[4]: landpattern.A[9],
                DQE[1]: landpattern.A[10],
                VSS[5]: landpattern.A[11],
                DQp[1][1]: landpattern.A[12],
                VSS[6]: landpattern.A[13],
                VSS[7]: landpattern.A[14],
                # Row B
                DQp[2][0]: landpattern.B[1],
                VSS[8]: landpattern.B[2],
                VSS[9]: landpattern.B[3],
                VDDQ[0]: landpattern.B[4],
                VSS[10]: landpattern.B[5],
                VDD[0]: landpattern.B[6],
                VSS[11]: landpattern.B[7],
                VSS[12]: landpattern.B[8],
                VDD[1]: landpattern.B[9],
                VSS[13]: landpattern.B[10],
                VDDQ[1]: landpattern.B[11],
                VSS[14]: landpattern.B[12],
                VSS[15]: landpattern.B[13],
                DQp[2][1]: landpattern.B[14],
                # Row C
                VSS[16]: landpattern.C[1],
                VSS[17]: landpattern.C[2],
                DQp[3][0]: landpattern.C[3],
                VSS[18]: landpattern.C[4],
                DQp[4][0]: landpattern.C[5],
                VSS[19]: landpattern.C[6],
                DQp[5][0]: landpattern.C[7],
                DQp[5][1]: landpattern.C[8],
                VSS[20]: landpattern.C[9],
                DQp[4][1]: landpattern.C[10],
                VSS[21]: landpattern.C[11],
                DQp[3][1]: landpattern.C[12],
                VSS[22]: landpattern.C[13],
                VSS[23]: landpattern.C[14],
                # Row D
                RCK_c[0]: landpattern.D[1],
                VDDQ[2]: landpattern.D[2],
                VSS[24]: landpattern.D[3],
                VDDQ[3]: landpattern.D[4],
                VSS[25]: landpattern.D[5],
                VDDQ[4]: landpattern.D[6],
                VSS[26]: landpattern.D[7],
                VSS[27]: landpattern.D[8],
                VDDQ[5]: landpattern.D[9],
                VSS[28]: landpattern.D[10],
                VDDQ[6]: landpattern.D[11],
                VSS[29]: landpattern.D[12],
                VDDQ[7]: landpattern.D[13],
                RCK_c[1]: landpattern.D[14],
                # Row E
                RCK_t[0]: landpattern.E[1],
                VSS[30]: landpattern.E[2],
                DQp[7][0]: landpattern.E[3],
                VSS[31]: landpattern.E[4],
                DQp[6][0]: landpattern.E[5],
                VSS[32]: landpattern.E[6],
                WCK_c[0]: landpattern.E[7],
                WCK_c[1]: landpattern.E[8],
                VSS[33]: landpattern.E[9],
                DQp[6][1]: landpattern.E[10],
                VSS[34]: landpattern.E[11],
                DQp[7][1]: landpattern.E[12],
                VSS[35]: landpattern.E[13],
                RCK_t[1]: landpattern.E[14],
                # Row F
                VSS[36]: landpattern.F[1],
                VDDQ[8]: landpattern.F[2],
                VSS[37]: landpattern.F[3],
                VDDQ[9]: landpattern.F[4],
                VSS[38]: landpattern.F[5],
                VSS[39]: landpattern.F[6],
                WCK_t[0]: landpattern.F[7],
                WCK_t[1]: landpattern.F[8],
                VSS[40]: landpattern.F[9],
                VSS[41]: landpattern.F[10],
                VDDQ[10]: landpattern.F[11],
                VSS[42]: landpattern.F[12],
                VDDQ[11]: landpattern.F[13],
                VSS[43]: landpattern.F[14],
                # Row G
                DQp[8][0]: landpattern.G[1],
                VSS[44]: landpattern.G[2],
                DQp[9][0]: landpattern.G[3],
                VSS[45]: landpattern.G[4],
                ERR[0]: landpattern.G[5],
                VDDQ[12]: landpattern.G[6],
                VSS[46]: landpattern.G[7],
                VSS[47]: landpattern.G[8],
                VDDQ[13]: landpattern.G[9],
                ERR[1]: landpattern.G[10],
                VSS[48]: landpattern.G[11],
                DQp[9][1]: landpattern.G[12],
                VSS[49]: landpattern.G[13],
                DQp[8][1]: landpattern.G[14],
                # Row H
                VSS[50]: landpattern.H[1],
                VSS[51]: landpattern.H[2],
                VSS[52]: landpattern.H[3],
                VDD[2]: landpattern.H[4],
                VSS[53]: landpattern.H[5],
                VDD[3]: landpattern.H[6],
                CA[0][0]: landpattern.H[7],
                CA[0][1]: landpattern.H[8],
                VDD[4]: landpattern.H[9],
                VSS[54]: landpattern.H[10],
                VDD[5]: landpattern.H[11],
                VSS[55]: landpattern.H[12],
                VSS[56]: landpattern.H[13],
                VSS[57]: landpattern.H[14],
                # Row J
                VPP[0]: landpattern.J[1],
                CA[4][0]: landpattern.J[2],
                VDD[6]: landpattern.J[3],
                CA[3][0]: landpattern.J[4],
                CA[2][0]: landpattern.J[5],
                VDD[7]: landpattern.J[6],
                CA[1][0]: landpattern.J[7],
                CA[1][1]: landpattern.J[8],
                VDD[8]: landpattern.J[9],
                CA[2][1]: landpattern.J[10],
                CA[3][1]: landpattern.J[11],
                VDD[9]: landpattern.J[12],
                CA[4][1]: landpattern.J[13],
                VPP[1]: landpattern.J[14],
                # Row K
                ZQ_AB: landpattern.K[1],
                RESET_n: landpattern.K[2],
                VSS[58]: landpattern.K[3],
                VSS[59]: landpattern.K[4],
                VDD[10]: landpattern.K[5],
                VSS[60]: landpattern.K[6],
                VSS[61]: landpattern.K[7],
                VSS[62]: landpattern.K[8],
                VSS[63]: landpattern.K[9],
                VDD[11]: landpattern.K[10],
                VSS[64]: landpattern.K[11],
                VSS[65]: landpattern.K[12],
                VSS[66]: landpattern.K[13],
                ZQ_CD: landpattern.K[14],
                # Row L
                VPP[2]: landpattern.L[1],
                CA[4][3]: landpattern.L[2],
                VDD[12]: landpattern.L[3],
                CA[3][3]: landpattern.L[4],
                CA[2][3]: landpattern.L[5],
                VDD[13]: landpattern.L[6],
                CA[1][3]: landpattern.L[7],
                CA[1][2]: landpattern.L[8],
                VDD[14]: landpattern.L[9],
                CA[2][2]: landpattern.L[10],
                CA[3][2]: landpattern.L[11],
                VDD[15]: landpattern.L[12],
                CA[4][2]: landpattern.L[13],
                VPP[3]: landpattern.L[14],
                # Row M
                VSS[67]: landpattern.M[1],
                VSS[68]: landpattern.M[2],
                VSS[69]: landpattern.M[3],
                VDD[16]: landpattern.M[4],
                VSS[70]: landpattern.M[5],
                VDD[17]: landpattern.M[6],
                CA[0][3]: landpattern.M[7],
                CA[0][2]: landpattern.M[8],
                VDD[18]: landpattern.M[9],
                VSS[71]: landpattern.M[10],
                VDD[19]: landpattern.M[11],
                VSS[72]: landpattern.M[12],
                VSS[73]: landpattern.M[13],
                VSS[74]: landpattern.M[14],
                # Row N
                DQp[8][3]: landpattern.N[1],
                VSS[75]: landpattern.N[2],
                DQp[9][3]: landpattern.N[3],
                VSS[76]: landpattern.N[4],
                ERR[3]: landpattern.N[5],
                VDDQ[14]: landpattern.N[6],
                VSS[77]: landpattern.N[7],
                VSS[78]: landpattern.N[8],
                VDDQ[15]: landpattern.N[9],
                ERR[2]: landpattern.N[10],
                VSS[79]: landpattern.N[11],
                DQp[9][2]: landpattern.N[12],
                VSS[80]: landpattern.N[13],
                DQp[8][2]: landpattern.N[14],
                # Row P
                VSS[81]: landpattern.P[1],
                VDDQ[16]: landpattern.P[2],
                VSS[82]: landpattern.P[3],
                VDDQ[17]: landpattern.P[4],
                VSS[83]: landpattern.P[5],
                VSS[84]: landpattern.P[6],
                WCK_t[3]: landpattern.P[7],
                WCK_t[2]: landpattern.P[8],
                VSS[85]: landpattern.P[9],
                VSS[86]: landpattern.P[10],
                VDDQ[18]: landpattern.P[11],
                VSS[87]: landpattern.P[12],
                VDDQ[19]: landpattern.P[13],
                VSS[88]: landpattern.P[14],
                # Row R
                RCK_t[3]: landpattern.R[1],
                VSS[89]: landpattern.R[2],
                DQp[7][3]: landpattern.R[3],
                VSS[90]: landpattern.R[4],
                DQp[6][3]: landpattern.R[5],
                VSS[91]: landpattern.R[6],
                WCK_c[3]: landpattern.R[7],
                WCK_c[2]: landpattern.R[8],
                VSS[92]: landpattern.R[9],
                DQp[6][2]: landpattern.R[10],
                VSS[93]: landpattern.R[11],
                DQp[7][2]: landpattern.R[12],
                VSS[94]: landpattern.R[13],
                RCK_t[2]: landpattern.R[14],
                # Row T
                RCK_c[3]: landpattern.T[1],
                VDDQ[20]: landpattern.T[2],
                VSS[95]: landpattern.T[3],
                VDDQ[21]: landpattern.T[4],
                VSS[96]: landpattern.T[5],
                VDDQ[22]: landpattern.T[6],
                VSS[97]: landpattern.T[7],
                VSS[98]: landpattern.T[8],
                VDDQ[23]: landpattern.T[9],
                VSS[99]: landpattern.T[10],
                VDDQ[24]: landpattern.T[11],
                VSS[100]: landpattern.T[12],
                VDDQ[25]: landpattern.T[13],
                RCK_c[2]: landpattern.T[14],
                # Row U
                VSS[101]: landpattern.U[1],
                VSS[102]: landpattern.U[2],
                DQp[3][3]: landpattern.U[3],
                VSS[103]: landpattern.U[4],
                DQp[4][3]: landpattern.U[5],
                VSS[104]: landpattern.U[6],
                DQp[5][3]: landpattern.U[7],
                DQp[5][2]: landpattern.U[8],
                VSS[105]: landpattern.U[9],
                DQp[4][2]: landpattern.U[10],
                VSS[106]: landpattern.U[11],
                DQp[3][2]: landpattern.U[12],
                VSS[107]: landpattern.U[13],
                VSS[108]: landpattern.U[14],
                # Row V
                DQp[2][3]: landpattern.V[1],
                VSS[109]: landpattern.V[2],
                VSS[110]: landpattern.V[3],
                VDDQ[26]: landpattern.V[4],
                VSS[111]: landpattern.V[5],
                VDD[20]: landpattern.V[6],
                VSS[112]: landpattern.V[7],
                VSS[113]: landpattern.V[8],
                VDD[21]: landpattern.V[9],
                VSS[114]: landpattern.V[10],
                VDDQ[27]: landpattern.V[11],
                VSS[115]: landpattern.V[12],
                VSS[116]: landpattern.V[13],
                DQp[2][2]: landpattern.V[14],
                # Row W
                VSS[117]: landpattern.W[1],
                VSS[118]: landpattern.W[2],
                DQp[1][3]: landpattern.W[3],
                VSS[119]: landpattern.W[4],
                DQE[3]: landpattern.W[5],
                VSS[120]: landpattern.W[6],
                DQp[0][3]: landpattern.W[7],
                DQp[0][2]: landpattern.W[8],
                VSS[121]: landpattern.W[9],
                DQE[2]: landpattern.W[10],
                VSS[122]: landpattern.W[11],
                DQp[1][2]: landpattern.W[12],
                VSS[123]: landpattern.W[13],
                VSS[124]: landpattern.W[14],
            }
        )
    ]


class GDDR7MemoryCircuit(Circuit):
    """GDDR7 Memory Circuit

    Exact translation of mem-device from jsl/examples/protocols/memory/gddr7/gddr7-src.stanza.
    Maps GDDR7 bundle to memory component pins.
    """

    io = GDDR7()
    pwr = Power()

    def __init__(self):
        self.mem = GDDR7MemoryComponent()

        topos = []

        # Map each of the 4 data channels - exact mapping from Stanza
        for i in range(4):
            # DQ signals (10 per channel)
            for j in range(10):
                topos.append(self.io.data[i].DQ[j] >> self.mem.DQp[j][i])

            # RCK differential pair
            topos.append(self.io.data[i].RCK.p >> self.mem.RCK_t[i])
            topos.append(self.io.data[i].RCK.n >> self.mem.RCK_c[i])

            # WCK differential pair
            topos.append(self.io.data[i].WCK.p >> self.mem.WCK_t[i])
            topos.append(self.io.data[i].WCK.n >> self.mem.WCK_c[i])

            # DQE
            topos.append(self.io.data[i].DQE >> self.mem.DQE[i])

            # ERR
            topos.append(self.io.data[i].ERR >> self.mem.ERR[i])

            # CA signals (5 per channel)
            for j in range(5):
                topos.append(self.io.data[i].CA[j] >> self.mem.CA[j][i])

        # Control signals
        topos.append(self.io.control.RESET_n >> self.mem.RESET_n)
        topos.append(self.io.control.ZQ_AB >> self.mem.ZQ_AB)
        topos.append(self.io.control.ZQ_CD >> self.mem.ZQ_CD)

        self.topos = topos


class GDDR7ICBGALandpattern(BGA):
    """30x30 BGA Landpattern for GDDR7 IC/GPU Component

    Exact translation from jsl/examples/protocols/memory/gddr7/gddr7-src.stanza:
    - 900-ball BGA (30 rows x 30 columns)
    - Pitch: 0.75mm
    - Ball diameter: 0.25mm
    - Package body: 24.0mm ± 0.1mm x 24.0mm ± 0.1mm x 0.71mm (+0.06/-0.0mm)
    - Density level B
    """

    def __init__(self):
        super().__init__(
            num_rows=30,
            num_cols=30,
            ball_diameter=0.25,
            pitch=0.75,
        )
        self.pad_config(SMDPadConfig())
        self.package_body(
            RectanglePackage(
                width=Toleranced(24.0, 0.1),
                length=Toleranced(24.0, 0.1),
                height=Toleranced.min_max(0.71, 0.71 + 0.06),
            )
        )
        self.density_level(DensityLevel.B)


def _signal_ball(row: int, col: int) -> bool:
    """Determine if a ball position is a signal ball or ground ball.

    Exact translation of signal-ball? from gddr7-src.stanza:
    ```stanza
    defn signal-ball? (a:Int b:Int) -> True|False :
      if a == 0 or a == 29 or b == 0 or b == 29 :
        true
      else :
        if (a * 30 + b + a % 2) % 2  == 0 :
          true
        else :
          false
    ```
    """
    if row == 0 or row == 29 or col == 0 or col == 29:
        return True
    else:
        if (row * 30 + col + row % 2) % 2 == 0:
            return True
        else:
            return False


# Reduced alphabet for BGA row naming (no I, O, Q, S, X, Z per JEDEC)
_REDUCED_ALPHA = "ABCDEFGHJKLMNPRTUVWY"


def _row_name(idx: int) -> str:
    """Convert row index to BGA row name using JEDEC reduced alphabet."""
    if idx < len(_REDUCED_ALPHA):
        return _REDUCED_ALPHA[idx]
    else:
        # For rows beyond single letter (AA, AB, etc.)
        first = idx // len(_REDUCED_ALPHA) - 1
        second = idx % len(_REDUCED_ALPHA)
        return _REDUCED_ALPHA[first] + _REDUCED_ALPHA[second]


class GDDR7ICComponent(Component):
    """GDDR7 GPU/IC Component

    Exact translation of ic-component from jsl/examples/protocols/memory/gddr7/gddr7-src.stanza.
    Large 30x30 BGA for GPU with GDDR7 interfaces.

    Uses checkerboard pattern for signal/ground balls.
    Signal pins count: 508 (edge + checkerboard pattern)
    Ground pins count: 392
    """

    reference_prefix = "U"
    mpn = "ic-JITX-GDDR7"
    description = "Dummy GDDR7 IC"

    # Signal pins (508 based on edge + checkerboard pattern)
    P = [Port() for _ in range(508)]

    # Ground pins (392 based on checkerboard pattern)
    GND = [Port() for _ in range(392)]

    landpattern = GDDR7ICBGALandpattern()
    symbol = BoxSymbol()


def _generate_ic_mapping():
    """Generate pad mapping using same algorithm as Stanza ic-component."""
    lp = GDDR7ICComponent.landpattern
    pad_map = {}
    sig_idx = 0
    gnd_idx = 0

    for row in range(30):
        row_letter = _row_name(row)
        for col in range(30):
            col_num = col + 1
            pad_ref = getattr(lp, row_letter)[col_num]

            if _signal_ball(row, col):
                pad_map[GDDR7ICComponent.P[sig_idx]] = pad_ref
                sig_idx += 1
            else:
                pad_map[GDDR7ICComponent.GND[gnd_idx]] = pad_ref
                gnd_idx += 1

    return pad_map


# Build the mapping after class definition
GDDR7ICComponent.mapping = [PadMapping(_generate_ic_mapping())]


class GDDR7ICCircuit(Circuit):
    """GDDR7 GPU/IC Circuit

    Exact translation of ic-device from jsl/examples/protocols/memory/gddr7/gddr7-src.stanza.
    Uses Provide pattern to expose GDDR7 interface (equivalent to Stanza's supports).
    """

    pwr = Power()

    def __init__(self):
        self.ic = GDDR7ICComponent()

        # Ground connections - create net connecting all GND pins
        gnd_net = self.pwr.Vn
        for gnd in self.ic.GND:
            gnd_net = gnd_net + gnd
        self.gnd_nets = gnd_net

        # Provide a GDDR7 interface using the generic P pins
        # This is equivalent to Stanza's "supports gddr7()"
        self.gddr7_provide = Provide(GDDR7()).one_of(
            lambda b: [self._create_gddr7_mapping(b)]
        )

    def _create_gddr7_mapping(self, b: GDDR7) -> dict:
        """Create mapping from GDDR7 bundle signals to IC generic pins.

        This is equivalent to Stanza's supports block that maps:
        - gddr7().data[i].DQ[j] => gen-io pins
        - gddr7().data[i].RCK => gen-io pins
        - etc.
        """
        mapping = {}
        pin_idx = 0

        # Map each of the 4 data channels
        for ch_idx in range(4):
            ch = b.data[ch_idx]

            # DQ signals (10 per channel)
            for dq_idx in range(10):
                mapping[ch.DQ[dq_idx]] = self.ic.P[pin_idx]
                pin_idx += 1

            # RCK (2 pins per channel)
            mapping[ch.RCK.p] = self.ic.P[pin_idx]
            pin_idx += 1
            mapping[ch.RCK.n] = self.ic.P[pin_idx]
            pin_idx += 1

            # WCK (2 pins per channel)
            mapping[ch.WCK.p] = self.ic.P[pin_idx]
            pin_idx += 1
            mapping[ch.WCK.n] = self.ic.P[pin_idx]
            pin_idx += 1

            # DQE
            mapping[ch.DQE] = self.ic.P[pin_idx]
            pin_idx += 1

            # ERR
            mapping[ch.ERR] = self.ic.P[pin_idx]
            pin_idx += 1

            # CA signals (5 per channel)
            for ca_idx in range(5):
                mapping[ch.CA[ca_idx]] = self.ic.P[pin_idx]
                pin_idx += 1

        # Control signals
        mapping[b.control.RESET_n] = self.ic.P[pin_idx]
        pin_idx += 1
        mapping[b.control.ZQ_AB] = self.ic.P[pin_idx]
        pin_idx += 1
        mapping[b.control.ZQ_CD] = self.ic.P[pin_idx]

        return mapping
