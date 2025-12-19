"""LPDDR5 Controller Components

Generic LPDDR5 controller component with Provide() pattern for pin optionality.
"""

from jitx import PadMapping, Provide
from jitx.circuit import Circuit
from jitx.component import Component
from jitx.common import Power
from jitx.net import Port
from jitx.toleranced import Toleranced

from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from ....protocols.memory.lpddr5 import LPDDR5, LPDDR5Width, LPDDR5Rank


class LPDDR5ControllerLandpattern(BGA):
    """22x22 BGA Landpattern for Generic LPDDR5 Controller

    Generic controller package for example purposes.
    """

    def __init__(self):
        super().__init__(
            num_rows=22,
            num_cols=22,
            ball_diameter=0.5,
            pitch=0.8,
        )
        self.pad_config(SMDPadConfig())
        self.package_body(
            RectanglePackage(
                width=Toleranced(18.0, 0.1),
                length=Toleranced(18.0, 0.1),
                height=Toleranced(1.0, 0.1),
            )
        )
        self.density_level(DensityLevel.B)


class LPDDR5ControllerComponent(Component):
    """Generic LPDDR5 Controller Component

    Generic controller for LPDDR5 x32 DualRank interface.
    Uses indexed ports matching the LPDDR5 bundle structure.
    """

    reference_prefix = "U"
    mpn = "LPDDR5-CTRL-GENERIC"
    manufacturer = "Generic"
    description = "Generic LPDDR5 controller"

    # Data - 32 bits (4 lanes x 8 bits)
    DQ = [Port() for _ in range(32)]

    # Write Clock (4 diff pairs = 8 pins)
    WCK_P = [Port() for _ in range(4)]
    WCK_N = [Port() for _ in range(4)]

    # Read Data Strobe (4 diff pairs = 8 pins)
    RDQS_P = [Port() for _ in range(4)]
    RDQS_N = [Port() for _ in range(4)]

    # Data Mask (4 pins)
    DMI = [Port() for _ in range(4)]

    # Clock (2 diff pairs = 4 pins)
    CK_P = [Port() for _ in range(2)]
    CK_N = [Port() for _ in range(2)]

    # Chip Select (4 pins: 2 channels x 2 ranks)
    CS = [Port() for _ in range(4)]

    # Command/Address (14 pins: 2 channels x 7 bits)
    CA = [Port() for _ in range(14)]

    # Control
    RESET_N = Port()

    # Power
    VDD = [Port() for _ in range(20)]
    VSS = [Port() for _ in range(60)]

    landpattern = LPDDR5ControllerLandpattern()
    symbol = BoxSymbol()

    mapping = [
        PadMapping(
            {
                # DQ pins (rows A-D)
                DQ[0]: landpattern.A[1],
                DQ[1]: landpattern.A[2],
                DQ[2]: landpattern.A[3],
                DQ[3]: landpattern.A[4],
                DQ[4]: landpattern.A[5],
                DQ[5]: landpattern.A[6],
                DQ[6]: landpattern.A[7],
                DQ[7]: landpattern.A[8],
                DQ[8]: landpattern.B[1],
                DQ[9]: landpattern.B[2],
                DQ[10]: landpattern.B[3],
                DQ[11]: landpattern.B[4],
                DQ[12]: landpattern.B[5],
                DQ[13]: landpattern.B[6],
                DQ[14]: landpattern.B[7],
                DQ[15]: landpattern.B[8],
                DQ[16]: landpattern.C[1],
                DQ[17]: landpattern.C[2],
                DQ[18]: landpattern.C[3],
                DQ[19]: landpattern.C[4],
                DQ[20]: landpattern.C[5],
                DQ[21]: landpattern.C[6],
                DQ[22]: landpattern.C[7],
                DQ[23]: landpattern.C[8],
                DQ[24]: landpattern.D[1],
                DQ[25]: landpattern.D[2],
                DQ[26]: landpattern.D[3],
                DQ[27]: landpattern.D[4],
                DQ[28]: landpattern.D[5],
                DQ[29]: landpattern.D[6],
                DQ[30]: landpattern.D[7],
                DQ[31]: landpattern.D[8],
                # WCK (diff pairs)
                WCK_P[0]: landpattern.E[1],
                WCK_N[0]: landpattern.E[2],
                WCK_P[1]: landpattern.E[3],
                WCK_N[1]: landpattern.E[4],
                WCK_P[2]: landpattern.E[5],
                WCK_N[2]: landpattern.E[6],
                WCK_P[3]: landpattern.E[7],
                WCK_N[3]: landpattern.E[8],
                # RDQS (diff pairs)
                RDQS_P[0]: landpattern.F[1],
                RDQS_N[0]: landpattern.F[2],
                RDQS_P[1]: landpattern.F[3],
                RDQS_N[1]: landpattern.F[4],
                RDQS_P[2]: landpattern.F[5],
                RDQS_N[2]: landpattern.F[6],
                RDQS_P[3]: landpattern.F[7],
                RDQS_N[3]: landpattern.F[8],
                # DMI
                DMI[0]: landpattern.G[1],
                DMI[1]: landpattern.G[2],
                DMI[2]: landpattern.G[3],
                DMI[3]: landpattern.G[4],
                # CK (diff pairs)
                CK_P[0]: landpattern.G[5],
                CK_N[0]: landpattern.G[6],
                CK_P[1]: landpattern.G[7],
                CK_N[1]: landpattern.G[8],
                # CS
                CS[0]: landpattern.H[1],
                CS[1]: landpattern.H[2],
                CS[2]: landpattern.H[3],
                CS[3]: landpattern.H[4],
                # CA
                CA[0]: landpattern.H[5],
                CA[1]: landpattern.H[6],
                CA[2]: landpattern.H[7],
                CA[3]: landpattern.H[8],
                CA[4]: landpattern.J[1],
                CA[5]: landpattern.J[2],
                CA[6]: landpattern.J[3],
                CA[7]: landpattern.J[4],
                CA[8]: landpattern.J[5],
                CA[9]: landpattern.J[6],
                CA[10]: landpattern.J[7],
                CA[11]: landpattern.J[8],
                CA[12]: landpattern.K[1],
                CA[13]: landpattern.K[2],
                # RESET_N
                RESET_N: landpattern.K[3],
                # VDD power pins
                VDD[0]: landpattern.A[9],
                VDD[1]: landpattern.A[10],
                VDD[2]: landpattern.A[11],
                VDD[3]: landpattern.A[12],
                VDD[4]: landpattern.B[9],
                VDD[5]: landpattern.B[10],
                VDD[6]: landpattern.B[11],
                VDD[7]: landpattern.B[12],
                VDD[8]: landpattern.C[9],
                VDD[9]: landpattern.C[10],
                VDD[10]: landpattern.C[11],
                VDD[11]: landpattern.C[12],
                VDD[12]: landpattern.D[9],
                VDD[13]: landpattern.D[10],
                VDD[14]: landpattern.D[11],
                VDD[15]: landpattern.D[12],
                VDD[16]: landpattern.E[9],
                VDD[17]: landpattern.E[10],
                VDD[18]: landpattern.E[11],
                VDD[19]: landpattern.E[12],
                # VSS ground pins
                VSS[0]: landpattern.A[13],
                VSS[1]: landpattern.A[14],
                VSS[2]: landpattern.A[15],
                VSS[3]: landpattern.A[16],
                VSS[4]: landpattern.A[17],
                VSS[5]: landpattern.A[18],
                VSS[6]: landpattern.A[19],
                VSS[7]: landpattern.A[20],
                VSS[8]: landpattern.A[21],
                VSS[9]: landpattern.A[22],
                VSS[10]: landpattern.B[13],
                VSS[11]: landpattern.B[14],
                VSS[12]: landpattern.B[15],
                VSS[13]: landpattern.B[16],
                VSS[14]: landpattern.B[17],
                VSS[15]: landpattern.B[18],
                VSS[16]: landpattern.B[19],
                VSS[17]: landpattern.B[20],
                VSS[18]: landpattern.B[21],
                VSS[19]: landpattern.B[22],
                VSS[20]: landpattern.C[13],
                VSS[21]: landpattern.C[14],
                VSS[22]: landpattern.C[15],
                VSS[23]: landpattern.C[16],
                VSS[24]: landpattern.C[17],
                VSS[25]: landpattern.C[18],
                VSS[26]: landpattern.C[19],
                VSS[27]: landpattern.C[20],
                VSS[28]: landpattern.C[21],
                VSS[29]: landpattern.C[22],
                VSS[30]: landpattern.D[13],
                VSS[31]: landpattern.D[14],
                VSS[32]: landpattern.D[15],
                VSS[33]: landpattern.D[16],
                VSS[34]: landpattern.D[17],
                VSS[35]: landpattern.D[18],
                VSS[36]: landpattern.D[19],
                VSS[37]: landpattern.D[20],
                VSS[38]: landpattern.D[21],
                VSS[39]: landpattern.D[22],
                VSS[40]: landpattern.E[13],
                VSS[41]: landpattern.E[14],
                VSS[42]: landpattern.E[15],
                VSS[43]: landpattern.E[16],
                VSS[44]: landpattern.E[17],
                VSS[45]: landpattern.E[18],
                VSS[46]: landpattern.E[19],
                VSS[47]: landpattern.E[20],
                VSS[48]: landpattern.E[21],
                VSS[49]: landpattern.E[22],
                VSS[50]: landpattern.F[9],
                VSS[51]: landpattern.F[10],
                VSS[52]: landpattern.F[11],
                VSS[53]: landpattern.F[12],
                VSS[54]: landpattern.F[13],
                VSS[55]: landpattern.F[14],
                VSS[56]: landpattern.F[15],
                VSS[57]: landpattern.F[16],
                VSS[58]: landpattern.F[17],
                VSS[59]: landpattern.F[18],
            }
        )
    ]


class LPDDR5ControllerCircuit(Circuit):
    """LPDDR5 Controller Module with Provide() Pattern

    Wraps LPDDR5ControllerComponent with Provide() for pin optionality.
    Uses LPDDR5 x32 DualRank configuration.
    """

    pwr = Power()

    def __init__(self):
        self.cpu = LPDDR5ControllerComponent()

        self._lpddr5_provide = Provide(
            LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank)
        ).one_of(lambda b: [self._create_lpddr5_mapping(b)])

    def _create_lpddr5_mapping(self, b: LPDDR5) -> dict:
        """Create mapping from LPDDR5 bundle to controller pins"""
        mapping = {}

        # Reset
        mapping[b.reset_n] = self.cpu.RESET_N

        # ======= Channel 0 =======
        # CK
        mapping[b.ck[0].p] = self.cpu.CK_P[0]
        mapping[b.ck[0].n] = self.cpu.CK_N[0]

        # CS (2 ranks)
        mapping[b.cs[0][0]] = self.cpu.CS[0]
        mapping[b.cs[0][1]] = self.cpu.CS[1]

        # CA (7 bits)
        for i in range(7):
            mapping[b.ca[0][i]] = self.cpu.CA[i]

        # Data Lane 0: DQ[0-7], WCK0, RDQS0, DMI0
        for i in range(8):
            mapping[b.d[0][0].dq[i]] = self.cpu.DQ[i]
        mapping[b.d[0][0].wck.p] = self.cpu.WCK_P[0]
        mapping[b.d[0][0].wck.n] = self.cpu.WCK_N[0]
        mapping[b.d[0][0].rdqs.p] = self.cpu.RDQS_P[0]
        mapping[b.d[0][0].rdqs.n] = self.cpu.RDQS_N[0]
        mapping[b.d[0][0].dmi] = self.cpu.DMI[0]

        # Data Lane 1: DQ[8-15], WCK1, RDQS1, DMI1
        for i in range(8):
            mapping[b.d[0][1].dq[i]] = self.cpu.DQ[8 + i]
        mapping[b.d[0][1].wck.p] = self.cpu.WCK_P[1]
        mapping[b.d[0][1].wck.n] = self.cpu.WCK_N[1]
        mapping[b.d[0][1].rdqs.p] = self.cpu.RDQS_P[1]
        mapping[b.d[0][1].rdqs.n] = self.cpu.RDQS_N[1]
        mapping[b.d[0][1].dmi] = self.cpu.DMI[1]

        # ======= Channel 1 =======
        # CK
        mapping[b.ck[1].p] = self.cpu.CK_P[1]
        mapping[b.ck[1].n] = self.cpu.CK_N[1]

        # CS (2 ranks)
        mapping[b.cs[1][0]] = self.cpu.CS[2]
        mapping[b.cs[1][1]] = self.cpu.CS[3]

        # CA (7 bits)
        for i in range(7):
            mapping[b.ca[1][i]] = self.cpu.CA[7 + i]

        # Data Lane 0: DQ[16-23], WCK2, RDQS2, DMI2
        for i in range(8):
            mapping[b.d[1][0].dq[i]] = self.cpu.DQ[16 + i]
        mapping[b.d[1][0].wck.p] = self.cpu.WCK_P[2]
        mapping[b.d[1][0].wck.n] = self.cpu.WCK_N[2]
        mapping[b.d[1][0].rdqs.p] = self.cpu.RDQS_P[2]
        mapping[b.d[1][0].rdqs.n] = self.cpu.RDQS_N[2]
        mapping[b.d[1][0].dmi] = self.cpu.DMI[2]

        # Data Lane 1: DQ[24-31], WCK3, RDQS3, DMI3
        for i in range(8):
            mapping[b.d[1][1].dq[i]] = self.cpu.DQ[24 + i]
        mapping[b.d[1][1].wck.p] = self.cpu.WCK_P[3]
        mapping[b.d[1][1].wck.n] = self.cpu.WCK_N[3]
        mapping[b.d[1][1].rdqs.p] = self.cpu.RDQS_P[3]
        mapping[b.d[1][1].rdqs.n] = self.cpu.RDQS_N[3]
        mapping[b.d[1][1].dmi] = self.cpu.DMI[3]

        return mapping


# Backwards compatibility aliases
LPDDR5ICComponent = LPDDR5ControllerComponent
LPDDR5ICCircuit = LPDDR5ControllerCircuit
