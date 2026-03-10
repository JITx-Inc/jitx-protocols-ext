"""DDR5 Example Components

JESD79-5 compliant DDR5 SDRAM components:

1. DDR5_x4x8_78ball  -- x4/x8, 78-ball MO-210-AL  (8.0 x 11.0 mm)
2. DDR5_x4x8_82ball  -- x4/x8, 82-ball MO-210-AN  (9.5 x 11.0 mm) [78 + 4 DNU]
3. DDR5_x16_102ball  -- x16,  102-ball MO-210-AT  (9.5 x 14.0 mm)
4. DDR5_x16_106ball  -- x16,  106-ball MO-210-AU  (9.5 x 14.0 mm) [102 + 4 DNU]

Ball assignments per JEDEC JESD79-5 Tables 1 & 2 and Figures 1 & 2.
All packages use split-BGA layouts with 0.8 mm pitch, 0.473 mm ball diameter,
0.42 mm SMD pad post-reflow.

Micron part numbers are used as representative MPNs; the ball assignments
are JEDEC-standard and apply to any compliant DDR5 SDRAM vendor.
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
# Grid planners for split-BGA packages
# =============================================================================


class SplitBGA_3col_Planner(GridPlanner):
    """Grid planner for split BGA with 3-column halves.

    Used by 78-ball (13x9) and 102-ball (17x9) packages.
    Cols 1-3 and 7-9 active; cols 4-6 (0-indexed: 3,4,5) are the gap.
    """

    def is_active(self, pos: GridPosition, num_rows: int, num_cols: int) -> bool | None:
        if pos.column in (3, 4, 5):
            return False
        return None


class SplitBGA_4col_Planner(GridPlanner):
    """Grid planner for split BGA with 4-column halves.

    Used by 82-ball (13x11) and 106-ball (17x11) packages.
    Cols 1-4 and 8-11 active; cols 5-7 (0-indexed: 4,5,6) are the gap.
    Additional outer columns only populated on first/last rows for DNU balls.
    """

    def __init__(self, extra_inactive: frozenset[tuple[int, int]] = frozenset()):
        super().__init__()
        self._extra_inactive = extra_inactive

    def is_active(self, pos: GridPosition, num_rows: int, num_cols: int) -> bool | None:
        if pos.column in (4, 5, 6):
            return False
        if (pos.row, pos.column) in self._extra_inactive:
            return False
        return None


def _support_ball_inactive(num_rows: int) -> frozenset[tuple[int, int]]:
    """Compute inactive positions for support-ball packages (82/106-ball).

    Cols 0 and 10 (0-indexed) are only populated on first and last rows.
    All interior rows have these columns inactive.
    """
    return frozenset(
        [(r, 0) for r in range(1, num_rows - 1)] + [(r, 10) for r in range(1, num_rows - 1)]
    )


_82BALL_EXTRA_INACTIVE = _support_ball_inactive(13)
_106BALL_EXTRA_INACTIVE = _support_ball_inactive(17)


# =============================================================================
# 78-ball DDR5 x4/x8: MO-210-AL (8.0 x 11.0 mm)
# =============================================================================
# JEDEC JESD79-5 Table 1 / Figure 1
# Grid: 13 rows (A-N, skip I) x 9 cols (1-3, gap 4-6, 7-9)
#
#      1       2       3       |  7          8       9
# A    LBDQ    VSS     VPP     |  ZQ         VSS     LBDQS
# B    VDD     VDDQ    DQ2     |  DQ3        VDDQ    VDD
# C    VSS     DQ0     DQS_t   |  DM_n/TDQS_t DQ1    VSS
# D    VDDQ    VSS     DQS_c   |  TDQS_c     VSS     VDDQ
# E    VDD     DQ4     DQ6     |  DQ7        DQ5     VDD
# F    VSS     VDDQ    VSS     |  VSS        VDDQ    VSS
# G    CA_ODT  MIR     VDD     |  CK_t       VDDQ    TEN
# H    ALERT_n VSS     CS_n    |  CK_c       VSS     VDD
# J    VDDQ    CA4     CA0     |  CA1        CA5     VDDQ
# K    VDD     CA6     CA2     |  CA3        CA7     VDD
# L    VDDQ    VSS     CA8     |  CA9        VSS     VDDQ
# M    CAI     CA10    CA12    |  CA13       CA11    RESET_n
# N    VDD     VSS     VDD     |  VPP        VSS     VDD


class DDR5_x4x8_78ball(jitx.Component):
    """DDR5 x4/x8 SDRAM -- 78-ball MO-210-AL (JESD79-5 Table 1)

    Package: 8.0 x 11.0 mm VFBGA, 0.8mm pitch, 78 balls.
    Representative MPN: Micron MT60B3G8RW-64B:B (24Gb, 3Gb x8, Die Rev B)
    """

    mpn = "MT60B3G8RW-64B:B"
    manufacturer = "Micron"
    reference_designator_prefix = "U"
    datasheet = "https://media-www.micron.com/-/media/client/global/documents/products/data-sheet/dram/ddr5/24gb_ddr5_sdram_dierevb.pdf"

    # -- Data (x8: DQ0-7, 1 DQS pair, DM/TDQS per JESD79-5 Table 3) --
    DQ = [Port() for _ in range(8)]
    DQS_t = Port()
    DQS_c = Port()
    DM_n = Port()  # C7: DM_n / TDQS_t (data mask or termination strobe true)
    TDQS_c = Port()  # D7: TDQS_c (termination strobe complement)

    # -- Loopback --
    LBDQ = Port()
    LBDQS = Port()

    # -- Command/Address --
    CA = [Port() for _ in range(14)]
    CK_t = Port()
    CK_c = Port()
    CS_n = Port()
    RESET_n = Port()

    # -- Control/Config --
    ALERT_n = Port()
    CA_ODT = Port()
    MIR = Port()
    CAI = Port()
    TEN = Port()
    ZQ = Port()

    # -- Power (counts verified: 11+11+16+2 = 40 power, 38 signal = 78) --
    VDD = [Port() for _ in range(11)]
    VDDQ = [Port() for _ in range(11)]
    VSS = [Port() for _ in range(16)]
    VPP = [Port() for _ in range(2)]

    def __init__(self):
        self.landpattern = (
            BGA(num_rows=13, num_cols=9, pitch=0.80, ball_diameter=0.42)
            .grid_planner(SplitBGA_3col_Planner())
            .pad_config(SMDPadConfig())
            .package_body(
                RectanglePackage(
                    width=Toleranced.min_max(7.9, 8.1),
                    length=Toleranced.min_max(10.9, 11.1),
                    height=Toleranced.min_max(0.8, 1.0),
                )
            )
        )

        self.symbol_data = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    *self.DQ,
                    self.DQS_t,
                    self.DQS_c,
                    self.DM_n,
                    self.TDQS_c,
                ),
                right=PinGroup(self.LBDQ, self.LBDQS, self.ZQ),
            ),
        )
        self.symbol_cmd = BoxSymbol(
            rows=Row(
                left=PinGroup(*self.CA),
                right=PinGroup(
                    self.CK_t,
                    self.CK_c,
                    self.CS_n,
                    self.RESET_n,
                    self.ALERT_n,
                    self.CA_ODT,
                    self.MIR,
                    self.CAI,
                    self.TEN,
                ),
            ),
        )
        self.symbol_power = BoxSymbol(
            columns=Column(
                up=PinGroup(*self.VDD, *self.VDDQ, *self.VPP),
                down=PinGroup(*self.VSS),
            ),
        )

        lp = self.landpattern
        self.mapping = [
            PadMapping(
                {
                    # Row A
                    self.LBDQ: lp.A[1],
                    self.VSS[0]: lp.A[2],
                    self.VPP[0]: lp.A[3],
                    self.ZQ: lp.A[7],
                    self.VSS[1]: lp.A[8],
                    self.LBDQS: lp.A[9],
                    # Row B
                    self.VDD[0]: lp.B[1],
                    self.VDDQ[0]: lp.B[2],
                    self.DQ[2]: lp.B[3],
                    self.DQ[3]: lp.B[7],
                    self.VDDQ[1]: lp.B[8],
                    self.VDD[1]: lp.B[9],
                    # Row C
                    self.VSS[2]: lp.C[1],
                    self.DQ[0]: lp.C[2],
                    self.DQS_t: lp.C[3],
                    self.DM_n: lp.C[7],
                    self.DQ[1]: lp.C[8],
                    self.VSS[3]: lp.C[9],
                    # Row D
                    self.VDDQ[2]: lp.D[1],
                    self.VSS[4]: lp.D[2],
                    self.DQS_c: lp.D[3],
                    self.TDQS_c: lp.D[7],
                    self.VSS[5]: lp.D[8],
                    self.VDDQ[3]: lp.D[9],
                    # Row E
                    self.VDD[2]: lp.E[1],
                    self.DQ[4]: lp.E[2],
                    self.DQ[6]: lp.E[3],
                    self.DQ[7]: lp.E[7],
                    self.DQ[5]: lp.E[8],
                    self.VDD[3]: lp.E[9],
                    # Row F
                    self.VSS[6]: lp.F[1],
                    self.VDDQ[4]: lp.F[2],
                    self.VSS[7]: lp.F[3],
                    self.VSS[8]: lp.F[7],
                    self.VDDQ[5]: lp.F[8],
                    self.VSS[9]: lp.F[9],
                    # Row G
                    self.CA_ODT: lp.G[1],
                    self.MIR: lp.G[2],
                    self.VDD[4]: lp.G[3],
                    self.CK_t: lp.G[7],
                    self.VDDQ[6]: lp.G[8],
                    self.TEN: lp.G[9],
                    # Row H
                    self.ALERT_n: lp.H[1],
                    self.VSS[10]: lp.H[2],
                    self.CS_n: lp.H[3],
                    self.CK_c: lp.H[7],
                    self.VSS[11]: lp.H[8],
                    self.VDD[5]: lp.H[9],
                    # Row J
                    self.VDDQ[7]: lp.J[1],
                    self.CA[4]: lp.J[2],
                    self.CA[0]: lp.J[3],
                    self.CA[1]: lp.J[7],
                    self.CA[5]: lp.J[8],
                    self.VDDQ[8]: lp.J[9],
                    # Row K
                    self.VDD[6]: lp.K[1],
                    self.CA[6]: lp.K[2],
                    self.CA[2]: lp.K[3],
                    self.CA[3]: lp.K[7],
                    self.CA[7]: lp.K[8],
                    self.VDD[7]: lp.K[9],
                    # Row L
                    self.VDDQ[9]: lp.L[1],
                    self.VSS[12]: lp.L[2],
                    self.CA[8]: lp.L[3],
                    self.CA[9]: lp.L[7],
                    self.VSS[13]: lp.L[8],
                    self.VDDQ[10]: lp.L[9],
                    # Row M
                    self.CAI: lp.M[1],
                    self.CA[10]: lp.M[2],
                    self.CA[12]: lp.M[3],
                    self.CA[13]: lp.M[7],
                    self.CA[11]: lp.M[8],
                    self.RESET_n: lp.M[9],
                    # Row N
                    self.VDD[8]: lp.N[1],
                    self.VSS[14]: lp.N[2],
                    self.VDD[9]: lp.N[3],
                    self.VPP[1]: lp.N[7],
                    self.VSS[15]: lp.N[8],
                    self.VDD[10]: lp.N[9],
                }
            )
        ]


# =============================================================================
# 82-ball DDR5 x4/x8: MO-210-AN (9.5 x 11.0 mm)
# =============================================================================
# JEDEC JESD79-5 Figure 1 (MO-210-AN with support balls)
# Grid: 13 rows (A-N) x 11 cols (1-4, gap 5-7, 8-11)
# Same 78 electrical balls as MO-210-AL, plus 4 DNU support balls at corners


class DDR5_x4x8_82ball(jitx.Component):
    """DDR5 x4/x8 SDRAM -- 82-ball MO-210-AN (JESD79-5 Figure 1)

    78 electrical balls + 4 DNU support balls at A1, A11, N1, N11.
    Package: 9.5 x 11.0 mm VFBGA, 0.8mm pitch, 82 balls.
    Representative MPN: Micron MT60B3G8JF-64B:C (24Gb, 3Gb x8, Die Rev C)
    """

    mpn = "MT60B3G8JF-64B:C"
    manufacturer = "Micron"
    reference_designator_prefix = "U"
    datasheet = "https://media-www.micron.com/-/media/client/global/documents/products/data-sheet/dram/ddr5/24gb_ddr5_sdram_dierevc.pdf"

    # -- Data --
    DQ = [Port() for _ in range(8)]
    DQS_t = Port()
    DQS_c = Port()
    DM_n = Port()
    TDQS_c = Port()

    # -- Loopback --
    LBDQ = Port()
    LBDQS = Port()

    # -- Command/Address --
    CA = [Port() for _ in range(14)]
    CK_t = Port()
    CK_c = Port()
    CS_n = Port()
    RESET_n = Port()

    # -- Control/Config --
    ALERT_n = Port()
    CA_ODT = Port()
    MIR = Port()
    CAI = Port()
    TEN = Port()
    ZQ = Port()

    # -- DNU (Do Not Use) support balls --
    DNU = [Port() for _ in range(4)]

    # -- Power --
    VDD = [Port() for _ in range(11)]
    VDDQ = [Port() for _ in range(11)]
    VSS = [Port() for _ in range(16)]
    VPP = [Port() for _ in range(2)]

    def __init__(self):
        self.landpattern = (
            BGA(num_rows=13, num_cols=11, pitch=0.80, ball_diameter=0.42)
            .grid_planner(SplitBGA_4col_Planner(_82BALL_EXTRA_INACTIVE))
            .pad_config(SMDPadConfig())
            .package_body(
                RectanglePackage(
                    width=Toleranced.min_max(9.4, 9.6),
                    length=Toleranced.min_max(10.9, 11.1),
                    height=Toleranced.min_max(0.8, 1.0),
                )
            )
        )

        self.symbol_data = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    *self.DQ,
                    self.DQS_t,
                    self.DQS_c,
                    self.DM_n,
                    self.TDQS_c,
                ),
                right=PinGroup(self.LBDQ, self.LBDQS, self.ZQ),
            ),
        )
        self.symbol_cmd = BoxSymbol(
            rows=Row(
                left=PinGroup(*self.CA),
                right=PinGroup(
                    self.CK_t,
                    self.CK_c,
                    self.CS_n,
                    self.RESET_n,
                    self.ALERT_n,
                    self.CA_ODT,
                    self.MIR,
                    self.CAI,
                    self.TEN,
                ),
            ),
        )
        self.symbol_power = BoxSymbol(
            columns=Column(
                up=PinGroup(*self.VDD, *self.VDDQ, *self.VPP),
                down=PinGroup(*self.VSS, *self.DNU),
            ),
        )

        lp = self.landpattern
        self.mapping = [
            PadMapping(
                {
                    # Row A (8 balls: includes DNU at cols 1, 11)
                    self.DNU[0]: lp.A[1],
                    self.LBDQ: lp.A[2],
                    self.VSS[0]: lp.A[3],
                    self.VPP[0]: lp.A[4],
                    self.ZQ: lp.A[8],
                    self.VSS[1]: lp.A[9],
                    self.LBDQS: lp.A[10],
                    self.DNU[1]: lp.A[11],
                    # Row B (6 balls: cols 2-4, 8-10)
                    self.VDD[0]: lp.B[2],
                    self.VDDQ[0]: lp.B[3],
                    self.DQ[2]: lp.B[4],
                    self.DQ[3]: lp.B[8],
                    self.VDDQ[1]: lp.B[9],
                    self.VDD[1]: lp.B[10],
                    # Row C
                    self.VSS[2]: lp.C[2],
                    self.DQ[0]: lp.C[3],
                    self.DQS_t: lp.C[4],
                    self.DM_n: lp.C[8],
                    self.DQ[1]: lp.C[9],
                    self.VSS[3]: lp.C[10],
                    # Row D
                    self.VDDQ[2]: lp.D[2],
                    self.VSS[4]: lp.D[3],
                    self.DQS_c: lp.D[4],
                    self.TDQS_c: lp.D[8],
                    self.VSS[5]: lp.D[9],
                    self.VDDQ[3]: lp.D[10],
                    # Row E
                    self.VDD[2]: lp.E[2],
                    self.DQ[4]: lp.E[3],
                    self.DQ[6]: lp.E[4],
                    self.DQ[7]: lp.E[8],
                    self.DQ[5]: lp.E[9],
                    self.VDD[3]: lp.E[10],
                    # Row F
                    self.VSS[6]: lp.F[2],
                    self.VDDQ[4]: lp.F[3],
                    self.VSS[7]: lp.F[4],
                    self.VSS[8]: lp.F[8],
                    self.VDDQ[5]: lp.F[9],
                    self.VSS[9]: lp.F[10],
                    # Row G
                    self.CA_ODT: lp.G[2],
                    self.MIR: lp.G[3],
                    self.VDD[4]: lp.G[4],
                    self.CK_t: lp.G[8],
                    self.VDDQ[6]: lp.G[9],
                    self.TEN: lp.G[10],
                    # Row H
                    self.ALERT_n: lp.H[2],
                    self.VSS[10]: lp.H[3],
                    self.CS_n: lp.H[4],
                    self.CK_c: lp.H[8],
                    self.VSS[11]: lp.H[9],
                    self.VDD[5]: lp.H[10],
                    # Row J
                    self.VDDQ[7]: lp.J[2],
                    self.CA[4]: lp.J[3],
                    self.CA[0]: lp.J[4],
                    self.CA[1]: lp.J[8],
                    self.CA[5]: lp.J[9],
                    self.VDDQ[8]: lp.J[10],
                    # Row K
                    self.VDD[6]: lp.K[2],
                    self.CA[6]: lp.K[3],
                    self.CA[2]: lp.K[4],
                    self.CA[3]: lp.K[8],
                    self.CA[7]: lp.K[9],
                    self.VDD[7]: lp.K[10],
                    # Row L
                    self.VDDQ[9]: lp.L[2],
                    self.VSS[12]: lp.L[3],
                    self.CA[8]: lp.L[4],
                    self.CA[9]: lp.L[8],
                    self.VSS[13]: lp.L[9],
                    self.VDDQ[10]: lp.L[10],
                    # Row M
                    self.CAI: lp.M[2],
                    self.CA[10]: lp.M[3],
                    self.CA[12]: lp.M[4],
                    self.CA[13]: lp.M[8],
                    self.CA[11]: lp.M[9],
                    self.RESET_n: lp.M[10],
                    # Row N (8 balls: includes DNU at cols 1, 11)
                    self.DNU[2]: lp.N[1],
                    self.VDD[8]: lp.N[2],
                    self.VSS[14]: lp.N[3],
                    self.VDD[9]: lp.N[4],
                    self.VPP[1]: lp.N[8],
                    self.VSS[15]: lp.N[9],
                    self.VDD[10]: lp.N[10],
                    self.DNU[3]: lp.N[11],
                }
            )
        ]


# =============================================================================
# 102-ball DDR5 x16: MO-210-AT (9.5 x 14.0 mm)
# =============================================================================
# JEDEC JESD79-5 Table 2 / Figure 2
# Grid: 17 rows (A-U, skip I,O,Q,S) x 9 cols (1-3, gap 4-6, 7-9)


class DDR5_x16_102ball(jitx.Component):
    """DDR5 x16 SDRAM -- 102-ball MO-210-AT (JESD79-5 Table 2)

    Package: 9.5 x 14.0 mm VFBGA, 0.8mm pitch, 102 balls.
    Representative MPN: Micron MT60B1536M16HZ-64B:C (24Gb, 1.5Gb x16, Die Rev C)
    """

    mpn = "MT60B1536M16HZ-64B:C"
    manufacturer = "Micron"
    reference_designator_prefix = "U"
    datasheet = "https://media-www.micron.com/-/media/client/global/documents/products/data-sheet/dram/ddr5/24gb_ddr5_sdram_dierevc.pdf"

    # -- Data upper byte (DQU0-7, DQSU pair, DMU_n) --
    DQU = [Port() for _ in range(8)]
    DQSU_t = Port()
    DQSU_c = Port()
    DMU_n = Port()

    # -- Data lower byte (DQL0-7, DQSL pair, DML_n) --
    DQL = [Port() for _ in range(8)]
    DQSL_t = Port()
    DQSL_c = Port()
    DML_n = Port()

    # -- Reserved --
    RFU = [Port() for _ in range(2)]

    # -- Loopback --
    LBDQ = Port()
    LBDQS = Port()

    # -- Command/Address --
    CA = [Port() for _ in range(14)]
    CK_t = Port()
    CK_c = Port()
    CS_n = Port()
    RESET_n = Port()

    # -- Control/Config --
    ALERT_n = Port()
    CA_ODT = Port()
    MIR = Port()
    CAI = Port()
    TEN = Port()
    ZQ = Port()

    # -- Power (counts: 15+15+20+2 = 52 power, 50 signal = 102) --
    VDD = [Port() for _ in range(15)]
    VDDQ = [Port() for _ in range(15)]
    VSS = [Port() for _ in range(20)]
    VPP = [Port() for _ in range(2)]

    def __init__(self):
        self.landpattern = (
            BGA(num_rows=17, num_cols=9, pitch=0.80, ball_diameter=0.42)
            .grid_planner(SplitBGA_3col_Planner())
            .pad_config(SMDPadConfig())
            .package_body(
                RectanglePackage(
                    width=Toleranced.min_max(9.4, 9.6),
                    length=Toleranced.min_max(13.9, 14.1),
                    height=Toleranced.min_max(0.8, 1.0),
                )
            )
        )

        self.symbol_data_upper = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    *self.DQU,
                    self.DQSU_t,
                    self.DQSU_c,
                    self.DMU_n,
                ),
                right=PinGroup(self.LBDQ, self.LBDQS, self.ZQ),
            ),
        )
        self.symbol_data_lower = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    *self.DQL,
                    self.DQSL_t,
                    self.DQSL_c,
                    self.DML_n,
                ),
                right=PinGroup(*self.RFU),
            ),
        )
        self.symbol_cmd = BoxSymbol(
            rows=Row(
                left=PinGroup(*self.CA),
                right=PinGroup(
                    self.CK_t,
                    self.CK_c,
                    self.CS_n,
                    self.RESET_n,
                    self.ALERT_n,
                    self.CA_ODT,
                    self.MIR,
                    self.CAI,
                    self.TEN,
                ),
            ),
        )
        self.symbol_power = BoxSymbol(
            columns=Column(
                up=PinGroup(*self.VDD, *self.VDDQ, *self.VPP),
                down=PinGroup(*self.VSS),
            ),
        )

        lp = self.landpattern
        self.mapping = [
            PadMapping(
                {
                    # Row A
                    self.LBDQ: lp.A[1],
                    self.VSS[0]: lp.A[2],
                    self.VPP[0]: lp.A[3],
                    self.ZQ: lp.A[7],
                    self.VSS[1]: lp.A[8],
                    self.LBDQS: lp.A[9],
                    # Row B
                    self.VDD[0]: lp.B[1],
                    self.VDDQ[0]: lp.B[2],
                    self.DQU[2]: lp.B[3],
                    self.DQU[3]: lp.B[7],
                    self.VDDQ[1]: lp.B[8],
                    self.VDD[1]: lp.B[9],
                    # Row C
                    self.VSS[2]: lp.C[1],
                    self.DQU[0]: lp.C[2],
                    self.DQSU_t: lp.C[3],
                    self.DMU_n: lp.C[7],
                    self.DQU[1]: lp.C[8],
                    self.VSS[3]: lp.C[9],
                    # Row D
                    self.VDDQ[2]: lp.D[1],
                    self.VSS[4]: lp.D[2],
                    self.DQSU_c: lp.D[3],
                    self.RFU[0]: lp.D[7],
                    self.VSS[5]: lp.D[8],
                    self.VDDQ[3]: lp.D[9],
                    # Row E
                    self.VDD[2]: lp.E[1],
                    self.DQU[4]: lp.E[2],
                    self.DQU[6]: lp.E[3],
                    self.DQU[7]: lp.E[7],
                    self.DQU[5]: lp.E[8],
                    self.VDD[3]: lp.E[9],
                    # Row F
                    self.VDD[4]: lp.F[1],
                    self.VDDQ[4]: lp.F[2],
                    self.DQL[2]: lp.F[3],
                    self.DQL[3]: lp.F[7],
                    self.VDDQ[5]: lp.F[8],
                    self.VDD[5]: lp.F[9],
                    # Row G
                    self.VSS[6]: lp.G[1],
                    self.DQL[0]: lp.G[2],
                    self.DQSL_t: lp.G[3],
                    self.DML_n: lp.G[7],
                    self.DQL[1]: lp.G[8],
                    self.VSS[7]: lp.G[9],
                    # Row H
                    self.VDDQ[6]: lp.H[1],
                    self.VSS[8]: lp.H[2],
                    self.DQSL_c: lp.H[3],
                    self.RFU[1]: lp.H[7],
                    self.VSS[9]: lp.H[8],
                    self.VDDQ[7]: lp.H[9],
                    # Row J
                    self.VDD[6]: lp.J[1],
                    self.DQL[4]: lp.J[2],
                    self.DQL[6]: lp.J[3],
                    self.DQL[7]: lp.J[7],
                    self.DQL[5]: lp.J[8],
                    self.VDD[7]: lp.J[9],
                    # Row K
                    self.VSS[10]: lp.K[1],
                    self.VDDQ[8]: lp.K[2],
                    self.VSS[11]: lp.K[3],
                    self.VSS[12]: lp.K[7],
                    self.VDDQ[9]: lp.K[8],
                    self.VSS[13]: lp.K[9],
                    # Row L
                    self.CA_ODT: lp.L[1],
                    self.MIR: lp.L[2],
                    self.VDD[8]: lp.L[3],
                    self.CK_t: lp.L[7],
                    self.VDDQ[10]: lp.L[8],
                    self.TEN: lp.L[9],
                    # Row M
                    self.ALERT_n: lp.M[1],
                    self.VSS[14]: lp.M[2],
                    self.CS_n: lp.M[3],
                    self.CK_c: lp.M[7],
                    self.VSS[15]: lp.M[8],
                    self.VDD[9]: lp.M[9],
                    # Row N
                    self.VDDQ[11]: lp.N[1],
                    self.CA[4]: lp.N[2],
                    self.CA[0]: lp.N[3],
                    self.CA[1]: lp.N[7],
                    self.CA[5]: lp.N[8],
                    self.VDDQ[12]: lp.N[9],
                    # Row P
                    self.VDD[10]: lp.P[1],
                    self.CA[6]: lp.P[2],
                    self.CA[2]: lp.P[3],
                    self.CA[3]: lp.P[7],
                    self.CA[7]: lp.P[8],
                    self.VDD[11]: lp.P[9],
                    # Row R
                    self.VDDQ[13]: lp.R[1],
                    self.VSS[16]: lp.R[2],
                    self.CA[8]: lp.R[3],
                    self.CA[9]: lp.R[7],
                    self.VSS[17]: lp.R[8],
                    self.VDDQ[14]: lp.R[9],
                    # Row T
                    self.CAI: lp.T[1],
                    self.CA[10]: lp.T[2],
                    self.CA[12]: lp.T[3],
                    self.CA[13]: lp.T[7],
                    self.CA[11]: lp.T[8],
                    self.RESET_n: lp.T[9],
                    # Row U
                    self.VDD[12]: lp.U[1],
                    self.VSS[18]: lp.U[2],
                    self.VDD[13]: lp.U[3],
                    self.VPP[1]: lp.U[7],
                    self.VSS[19]: lp.U[8],
                    self.VDD[14]: lp.U[9],
                }
            )
        ]


# =============================================================================
# 106-ball DDR5 x16: MO-210-AU (9.5 x 14.0 mm)
# =============================================================================
# JEDEC JESD79-5 Figure 2 (MO-210-TBD with support balls)
# Grid: 17 rows (A-U) x 11 cols (1-4, gap 5-7, 8-11)
# Same 102 electrical balls as MO-210-AT, plus 4 DNU support balls at corners


class DDR5_x16_106ball(jitx.Component):
    """DDR5 x16 SDRAM -- 106-ball MO-210-AU (JESD79-5 Figure 2)

    102 electrical balls + 4 DNU support balls at A1, A11, U1, U11.
    Package: 9.5 x 14.0 mm VFBGA, 0.8mm pitch, 106 balls.
    Representative MPN: Micron MT60B1536M16HZ-64B:C (24Gb, 1.5Gb x16, Die Rev C)
    """

    mpn = "MT60B1536M16HZ-64B:C"
    manufacturer = "Micron"
    reference_designator_prefix = "U"
    datasheet = "https://media-www.micron.com/-/media/client/global/documents/products/data-sheet/dram/ddr5/24gb_ddr5_sdram_dierevc.pdf"

    # -- Data upper byte --
    DQU = [Port() for _ in range(8)]
    DQSU_t = Port()
    DQSU_c = Port()
    DMU_n = Port()

    # -- Data lower byte --
    DQL = [Port() for _ in range(8)]
    DQSL_t = Port()
    DQSL_c = Port()
    DML_n = Port()

    # -- Reserved --
    RFU = [Port() for _ in range(2)]

    # -- Loopback --
    LBDQ = Port()
    LBDQS = Port()

    # -- Command/Address --
    CA = [Port() for _ in range(14)]
    CK_t = Port()
    CK_c = Port()
    CS_n = Port()
    RESET_n = Port()

    # -- Control/Config --
    ALERT_n = Port()
    CA_ODT = Port()
    MIR = Port()
    CAI = Port()
    TEN = Port()
    ZQ = Port()

    # -- DNU support balls --
    DNU = [Port() for _ in range(4)]

    # -- Power --
    VDD = [Port() for _ in range(15)]
    VDDQ = [Port() for _ in range(15)]
    VSS = [Port() for _ in range(20)]
    VPP = [Port() for _ in range(2)]

    def __init__(self):
        self.landpattern = (
            BGA(num_rows=17, num_cols=11, pitch=0.80, ball_diameter=0.42)
            .grid_planner(SplitBGA_4col_Planner(_106BALL_EXTRA_INACTIVE))
            .pad_config(SMDPadConfig())
            .package_body(
                RectanglePackage(
                    width=Toleranced.min_max(9.4, 9.6),
                    length=Toleranced.min_max(13.9, 14.1),
                    height=Toleranced.min_max(0.8, 1.0),
                )
            )
        )

        self.symbol_data_upper = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    *self.DQU,
                    self.DQSU_t,
                    self.DQSU_c,
                    self.DMU_n,
                ),
                right=PinGroup(self.LBDQ, self.LBDQS, self.ZQ),
            ),
        )
        self.symbol_data_lower = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    *self.DQL,
                    self.DQSL_t,
                    self.DQSL_c,
                    self.DML_n,
                ),
                right=PinGroup(*self.RFU),
            ),
        )
        self.symbol_cmd = BoxSymbol(
            rows=Row(
                left=PinGroup(*self.CA),
                right=PinGroup(
                    self.CK_t,
                    self.CK_c,
                    self.CS_n,
                    self.RESET_n,
                    self.ALERT_n,
                    self.CA_ODT,
                    self.MIR,
                    self.CAI,
                    self.TEN,
                ),
            ),
        )
        self.symbol_power = BoxSymbol(
            columns=Column(
                up=PinGroup(*self.VDD, *self.VDDQ, *self.VPP),
                down=PinGroup(*self.VSS, *self.DNU),
            ),
        )

        lp = self.landpattern
        self.mapping = [
            PadMapping(
                {
                    # Row A (8 balls: DNU at cols 1, 11)
                    self.DNU[0]: lp.A[1],
                    self.LBDQ: lp.A[2],
                    self.VSS[0]: lp.A[3],
                    self.VPP[0]: lp.A[4],
                    self.ZQ: lp.A[8],
                    self.VSS[1]: lp.A[9],
                    self.LBDQS: lp.A[10],
                    self.DNU[1]: lp.A[11],
                    # Row B
                    self.VDD[0]: lp.B[2],
                    self.VDDQ[0]: lp.B[3],
                    self.DQU[2]: lp.B[4],
                    self.DQU[3]: lp.B[8],
                    self.VDDQ[1]: lp.B[9],
                    self.VDD[1]: lp.B[10],
                    # Row C
                    self.VSS[2]: lp.C[2],
                    self.DQU[0]: lp.C[3],
                    self.DQSU_t: lp.C[4],
                    self.DMU_n: lp.C[8],
                    self.DQU[1]: lp.C[9],
                    self.VSS[3]: lp.C[10],
                    # Row D
                    self.VDDQ[2]: lp.D[2],
                    self.VSS[4]: lp.D[3],
                    self.DQSU_c: lp.D[4],
                    self.RFU[0]: lp.D[8],
                    self.VSS[5]: lp.D[9],
                    self.VDDQ[3]: lp.D[10],
                    # Row E
                    self.VDD[2]: lp.E[2],
                    self.DQU[4]: lp.E[3],
                    self.DQU[6]: lp.E[4],
                    self.DQU[7]: lp.E[8],
                    self.DQU[5]: lp.E[9],
                    self.VDD[3]: lp.E[10],
                    # Row F
                    self.VDD[4]: lp.F[2],
                    self.VDDQ[4]: lp.F[3],
                    self.DQL[2]: lp.F[4],
                    self.DQL[3]: lp.F[8],
                    self.VDDQ[5]: lp.F[9],
                    self.VDD[5]: lp.F[10],
                    # Row G
                    self.VSS[6]: lp.G[2],
                    self.DQL[0]: lp.G[3],
                    self.DQSL_t: lp.G[4],
                    self.DML_n: lp.G[8],
                    self.DQL[1]: lp.G[9],
                    self.VSS[7]: lp.G[10],
                    # Row H
                    self.VDDQ[6]: lp.H[2],
                    self.VSS[8]: lp.H[3],
                    self.DQSL_c: lp.H[4],
                    self.RFU[1]: lp.H[8],
                    self.VSS[9]: lp.H[9],
                    self.VDDQ[7]: lp.H[10],
                    # Row J
                    self.VDD[6]: lp.J[2],
                    self.DQL[4]: lp.J[3],
                    self.DQL[6]: lp.J[4],
                    self.DQL[7]: lp.J[8],
                    self.DQL[5]: lp.J[9],
                    self.VDD[7]: lp.J[10],
                    # Row K
                    self.VSS[10]: lp.K[2],
                    self.VDDQ[8]: lp.K[3],
                    self.VSS[11]: lp.K[4],
                    self.VSS[12]: lp.K[8],
                    self.VDDQ[9]: lp.K[9],
                    self.VSS[13]: lp.K[10],
                    # Row L
                    self.CA_ODT: lp.L[2],
                    self.MIR: lp.L[3],
                    self.VDD[8]: lp.L[4],
                    self.CK_t: lp.L[8],
                    self.VDDQ[10]: lp.L[9],
                    self.TEN: lp.L[10],
                    # Row M
                    self.ALERT_n: lp.M[2],
                    self.VSS[14]: lp.M[3],
                    self.CS_n: lp.M[4],
                    self.CK_c: lp.M[8],
                    self.VSS[15]: lp.M[9],
                    self.VDD[9]: lp.M[10],
                    # Row N
                    self.VDDQ[11]: lp.N[2],
                    self.CA[4]: lp.N[3],
                    self.CA[0]: lp.N[4],
                    self.CA[1]: lp.N[8],
                    self.CA[5]: lp.N[9],
                    self.VDDQ[12]: lp.N[10],
                    # Row P
                    self.VDD[10]: lp.P[2],
                    self.CA[6]: lp.P[3],
                    self.CA[2]: lp.P[4],
                    self.CA[3]: lp.P[8],
                    self.CA[7]: lp.P[9],
                    self.VDD[11]: lp.P[10],
                    # Row R
                    self.VDDQ[13]: lp.R[2],
                    self.VSS[16]: lp.R[3],
                    self.CA[8]: lp.R[4],
                    self.CA[9]: lp.R[8],
                    self.VSS[17]: lp.R[9],
                    self.VDDQ[14]: lp.R[10],
                    # Row T
                    self.CAI: lp.T[2],
                    self.CA[10]: lp.T[3],
                    self.CA[12]: lp.T[4],
                    self.CA[13]: lp.T[8],
                    self.CA[11]: lp.T[9],
                    self.RESET_n: lp.T[10],
                    # Row U (8 balls: DNU at cols 1, 11)
                    self.DNU[2]: lp.U[1],
                    self.VDD[12]: lp.U[2],
                    self.VSS[18]: lp.U[3],
                    self.VDD[13]: lp.U[4],
                    self.VPP[1]: lp.U[8],
                    self.VSS[19]: lp.U[9],
                    self.VDD[14]: lp.U[10],
                    self.DNU[3]: lp.U[11],
                }
            )
        ]


# =============================================================================
# Backward-compatible aliases
# =============================================================================

DDR5Memory = DDR5_x4x8_78ball


# =============================================================================
# Circuit wrappers (for example designs)
# =============================================================================


class DDR5MemoryCircuit_x8(Circuit):
    """DDR5 Memory Circuit wrapping an x8 component with DDR5 bundle IO.

    Wires the external DDR5 bundle (io) to the internal DRAM component's
    physical pins, enabling topology connections from the example design
    to reach the actual BGA pads.
    """

    io = DDR5(DDR5Width.x8, DDR5Rank.SingleRank)
    pwr = Power()

    def __init__(self, component_cls: type = DDR5_x4x8_82ball):
        self.mem = component_cls()

        # -- Power wiring --
        gnd_net = self.pwr.Vn
        for p in self.mem.VSS:
            gnd_net = gnd_net + p
        self.vss_net = gnd_net

        vdd_net = self.pwr.Vp
        for p in self.mem.VDD:
            vdd_net = vdd_net + p
        self.vdd_net = vdd_net

        vddq_net = self.mem.VDDQ[0]
        for p in self.mem.VDDQ[1:]:
            vddq_net = vddq_net + p
        self.vddq_net = vddq_net

        vpp_net = self.mem.VPP[0]
        for p in self.mem.VPP[1:]:
            vpp_net = vpp_net + p
        self.vpp_net = vpp_net

        # -- Data topology: io bundle >> component pins --
        # Using >> so SI constraints chain through to BGA pads
        self.dq_topos = [self.io.data.DQ[i] >> self.mem.DQ[i] for i in range(8)]
        self.dqs_p_topo = self.io.data.DQS[0].p >> self.mem.DQS_t
        self.dqs_n_topo = self.io.data.DQS[0].n >> self.mem.DQS_c
        self.dmi_topo = self.io.data.DMI[0] >> self.mem.DM_n

        # -- CA topology: io bundle >> component pins --
        self.ck_p_topo = self.io.ca.CK.p >> self.mem.CK_t
        self.ck_n_topo = self.io.ca.CK.n >> self.mem.CK_c
        self.ca_topos = [self.io.ca.CA[i] >> self.mem.CA[i] for i in range(14)]
        self.cs_topo = self.io.ca.CS_n[0] >> self.mem.CS_n
        self.reset_topo = self.io.ca.RESET_n >> self.mem.RESET_n
        self.alert_topo = self.io.ca.ALERT_n >> self.mem.ALERT_n


class DDR5MemoryCircuit_x16(Circuit):
    """DDR5 Memory Circuit wrapping the x16 102-ball component.

    Wires the external DDR5 x16 bundle (io) to the internal DRAM component's
    physical pins. The x16 device has two byte lanes:
    - Lower byte: DQL[0:7], DQSL_t/c, DML_n  -> bundle DQ[0:7], DQS[0], DMI[0]
    - Upper byte: DQU[0:7], DQSU_t/c, DMU_n  -> bundle DQ[8:15], DQS[1], DMI[1]
    """

    io = DDR5(DDR5Width.x16, DDR5Rank.SingleRank)
    pwr = Power()

    def __init__(self):
        self.mem = DDR5_x16_102ball()

        # -- Power wiring --
        gnd_net = self.pwr.Vn
        for p in self.mem.VSS:
            gnd_net = gnd_net + p
        self.vss_net = gnd_net

        vdd_net = self.pwr.Vp
        for p in self.mem.VDD:
            vdd_net = vdd_net + p
        self.vdd_net = vdd_net

        vddq_net = self.mem.VDDQ[0]
        for p in self.mem.VDDQ[1:]:
            vddq_net = vddq_net + p
        self.vddq_net = vddq_net

        vpp_net = self.mem.VPP[0]
        for p in self.mem.VPP[1:]:
            vpp_net = vpp_net + p
        self.vpp_net = vpp_net

        # -- Data topology: io bundle >> component pins --
        # Using >> so SI constraints chain through to BGA pads
        # Lower byte: DQ[0:7] >> DQL[0:7]
        self.dq_topos_lower = [self.io.data.DQ[i] >> self.mem.DQL[i] for i in range(8)]
        # Upper byte: DQ[8:15] >> DQU[0:7]
        self.dq_topos_upper = [self.io.data.DQ[8 + i] >> self.mem.DQU[i] for i in range(8)]
        # Lower byte strobe
        self.dqsl_p_topo = self.io.data.DQS[0].p >> self.mem.DQSL_t
        self.dqsl_n_topo = self.io.data.DQS[0].n >> self.mem.DQSL_c
        # Upper byte strobe
        self.dqsu_p_topo = self.io.data.DQS[1].p >> self.mem.DQSU_t
        self.dqsu_n_topo = self.io.data.DQS[1].n >> self.mem.DQSU_c
        # Byte masks
        self.dml_topo = self.io.data.DMI[0] >> self.mem.DML_n
        self.dmu_topo = self.io.data.DMI[1] >> self.mem.DMU_n

        # -- CA topology: io bundle >> component pins --
        self.ck_p_topo = self.io.ca.CK.p >> self.mem.CK_t
        self.ck_n_topo = self.io.ca.CK.n >> self.mem.CK_c
        self.ca_topos = [self.io.ca.CA[i] >> self.mem.CA[i] for i in range(14)]
        self.cs_topo = self.io.ca.CS_n[0] >> self.mem.CS_n
        self.reset_topo = self.io.ca.RESET_n >> self.mem.RESET_n
        self.alert_topo = self.io.ca.ALERT_n >> self.mem.ALERT_n


DDR5MemoryCircuit = DDR5MemoryCircuit_x8


# =============================================================================
# DDR5 Controllers (dummy for examples)
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
    if idx < len(_CTRL_REDUCED_ALPHA):
        return _CTRL_REDUCED_ALPHA[idx]
    first = idx // len(_CTRL_REDUCED_ALPHA) - 1
    second = idx % len(_CTRL_REDUCED_ALPHA)
    return _CTRL_REDUCED_ALPHA[first] + _CTRL_REDUCED_ALPHA[second]


class DDR5ControllerComponent_x8(Component):
    """DDR5 Controller -- dummy controller with DDR5 x8 interface."""

    reference_designator_prefix = "U"
    mpn = "JITX-DDR5-CTRL-X8"
    description = "Dummy DDR5 x8 controller"

    DQ = [Port() for _ in range(8)]
    DQS_P = Port()
    DQS_N = Port()
    DMI = Port()
    CK_P = Port()
    CK_N = Port()
    CA = [Port() for _ in range(14)]
    CS_N = Port()
    RESET_N = Port()
    ALERT_N = Port()
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(40)]
    VDDQ = [Port() for _ in range(8)]

    landpattern = DDR5ControllerBGALandpattern()
    symbol = BoxSymbol()


def _gen_x8_ctrl_mapping():
    lp = DDR5ControllerComponent_x8.landpattern
    C = DDR5ControllerComponent_x8
    all_ports = [
        *C.DQ,
        C.DQS_P,
        C.DQS_N,
        C.DMI,
        C.CK_P,
        C.CK_N,
        *C.CA,
        C.CS_N,
        C.RESET_N,
        C.ALERT_N,
        *C.VDD,
        *C.VSS,
        *C.VDDQ,
    ]
    pad_map = {}
    pad_idx = 0
    for row in range(20):
        row_letter = _ctrl_row_name(row)
        for col in range(20):
            if pad_idx < len(all_ports):
                pad_map[all_ports[pad_idx]] = getattr(lp, row_letter)[col + 1]
                pad_idx += 1
    return pad_map


DDR5ControllerComponent_x8.mapping = [PadMapping(_gen_x8_ctrl_mapping())]

# Backward-compatible alias
DDR5ControllerComponent = DDR5ControllerComponent_x8


class DDR5ControllerComponent_x16(Component):
    """DDR5 Controller -- dummy controller with DDR5 x16 interface."""

    reference_designator_prefix = "U"
    mpn = "JITX-DDR5-CTRL-X16"
    description = "Dummy DDR5 x16 controller"

    DQ = [Port() for _ in range(16)]
    DQS_P = [Port() for _ in range(2)]
    DQS_N = [Port() for _ in range(2)]
    DMI = [Port() for _ in range(2)]
    CK_P = Port()
    CK_N = Port()
    CA = [Port() for _ in range(14)]
    CS_N = Port()
    RESET_N = Port()
    ALERT_N = Port()
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(40)]
    VDDQ = [Port() for _ in range(8)]

    landpattern = DDR5ControllerBGALandpattern()
    symbol = BoxSymbol()


def _gen_x16_ctrl_mapping():
    lp = DDR5ControllerComponent_x16.landpattern
    C = DDR5ControllerComponent_x16
    all_ports = [
        *C.DQ,
        *C.DQS_P,
        *C.DQS_N,
        *C.DMI,
        C.CK_P,
        C.CK_N,
        *C.CA,
        C.CS_N,
        C.RESET_N,
        C.ALERT_N,
        *C.VDD,
        *C.VSS,
        *C.VDDQ,
    ]
    pad_map = {}
    pad_idx = 0
    for row in range(20):
        row_letter = _ctrl_row_name(row)
        for col in range(20):
            if pad_idx < len(all_ports):
                pad_map[all_ports[pad_idx]] = getattr(lp, row_letter)[col + 1]
                pad_idx += 1
    return pad_map


DDR5ControllerComponent_x16.mapping = [PadMapping(_gen_x16_ctrl_mapping())]


class DDR5ControllerCircuit(Circuit):
    """DDR5 Controller Circuit with Provide pattern -- x8 interface."""

    pwr = Power()

    def __init__(self):
        self.ctrl = DDR5ControllerComponent_x8()

        self.ddr5_provide = Provide(DDR5(DDR5Width.x8, DDR5Rank.SingleRank)).one_of(
            lambda b: [self._create_ddr5_mapping(b)]
        )

    def _create_ddr5_mapping(self, b: DDR5) -> dict:
        mapping = {}
        for i in range(8):
            mapping[b.data.DQ[i]] = self.ctrl.DQ[i]
        mapping[b.data.DQS[0].p] = self.ctrl.DQS_P
        mapping[b.data.DQS[0].n] = self.ctrl.DQS_N
        mapping[b.data.DMI[0]] = self.ctrl.DMI
        for i in range(14):
            mapping[b.ca.CA[i]] = self.ctrl.CA[i]
        mapping[b.ca.CK.p] = self.ctrl.CK_P
        mapping[b.ca.CK.n] = self.ctrl.CK_N
        mapping[b.ca.CS_n[0]] = self.ctrl.CS_N
        mapping[b.ca.RESET_n] = self.ctrl.RESET_N
        mapping[b.ca.ALERT_n] = self.ctrl.ALERT_N
        return mapping


class DDR5ControllerCircuit_x16(Circuit):
    """DDR5 Controller Circuit with Provide pattern -- x16 interface."""

    pwr = Power()

    def __init__(self):
        self.ctrl = DDR5ControllerComponent_x16()

        self.ddr5_provide = Provide(DDR5(DDR5Width.x16, DDR5Rank.SingleRank)).one_of(
            lambda b: [self._create_ddr5_mapping(b)]
        )

    def _create_ddr5_mapping(self, b: DDR5) -> dict:
        mapping = {}
        for i in range(16):
            mapping[b.data.DQ[i]] = self.ctrl.DQ[i]
        for i in range(2):
            mapping[b.data.DQS[i].p] = self.ctrl.DQS_P[i]
            mapping[b.data.DQS[i].n] = self.ctrl.DQS_N[i]
            mapping[b.data.DMI[i]] = self.ctrl.DMI[i]
        for i in range(14):
            mapping[b.ca.CA[i]] = self.ctrl.CA[i]
        mapping[b.ca.CK.p] = self.ctrl.CK_P
        mapping[b.ca.CK.n] = self.ctrl.CK_N
        mapping[b.ca.CS_n[0]] = self.ctrl.CS_N
        mapping[b.ca.RESET_n] = self.ctrl.RESET_N
        mapping[b.ca.ALERT_n] = self.ctrl.ALERT_N
        return mapping
