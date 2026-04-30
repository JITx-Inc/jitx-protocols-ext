"""Xilinx Versal protocol bundles.

Python translation of `bundles/versal.stanza`. Each bundle here mirrors the
stanza definition exactly — same sub-port names, same shapes, same arities.

Used by `examples/protocols/memory/xc2ve3858_components.py` (and any future
Versal devices) to expose protocol-bank ports on the circuit boundary.

Stanza source: `customers/lockheed-martin/tssr-parts/xilinx/bundles/versal.stanza`

Note on naming: stanza uses upper-case sub-port names (`TX`, `RX`, `P`, `N`,
`REFCLK`, `L`, `VCCO`, `VCCIO`, `VCC`). Python conventionally uses lower-case
attribute names, but the existing `LanePair` (`TX`, `RX`) and `Power`
(`Vp`, `Vn`) bundles in `jitx.common` already preserve the upper-case style.
We keep the stanza casing throughout for one-to-one mapping with the source.

`DiffPair` from `jitx.net` uses lower-case `p`/`n`; that is the Python
convention even though stanza has `P`/`N`. Net wiring in the consumer
component compensates by mapping stanza `XYZ.P` -> Python `xyz.p`.
"""

from __future__ import annotations

from collections.abc import Sequence

from jitx.common import LanePair, Power
from jitx.net import DiffPair, Port


# Stanza `clk-diff-pair` is structurally identical to `diff-pair`. The alias
# exists in stanza only for documentation. We keep `DiffPair` directly to
# avoid an empty subclass.
ClkDiffPair = DiffPair


class GTYPQuad(Port):
    """Versal GTYP transceiver quad (4 lanes + 2 reference clocks).

    Stanza:

        pcb-bundle gtyp-quad :
          port L : lane-pair[4]
          port REFCLK : clk-diff-pair[2]
    """

    L: Sequence[LanePair]
    REFCLK: Sequence[DiffPair]

    def __init__(self):
        self.L = tuple(LanePair() for _ in range(4))
        self.REFCLK = tuple(DiffPair() for _ in range(2))


class GTYPMMIQuad(GTYPQuad):
    """Versal GTYP MMI quad (multi-mode I/O variant of GTYPQuad).

    Structurally identical to `GTYPQuad`; kept distinct so that pin
    assignment can match the bank-105-only specialization in stanza.
    """


class HDIOBank(Port):
    """Versal High-Density I/O bank (11 differential pairs + 1 VCCO rail).

    Stanza:

        pcb-bundle hdio-bank :
          port L : diff-pair[11]
          port VCCO : power
    """

    L: Sequence[DiffPair]
    VCCO = Power()

    def __init__(self):
        self.L = tuple(DiffPair() for _ in range(11))


class PMCMioBank(Port):
    """Versal PMC MIO bank (26 single-ended pins + 1 VCCO rail).

    Stanza:

        pcb-bundle pmc-mio-bank :
          port P : pin[26]
          port VCCO : power
    """

    P: Sequence[Port]
    VCCO = Power()

    def __init__(self):
        self.P = tuple(Port() for _ in range(26))


class LPDMioBank(Port):
    """Versal LPD MIO bank (26 single-ended pins + 1 VCCO rail).

    Stanza:

        pcb-bundle lpd-mio-bank :
          port P : pin[26]
          port VCCO : power
    """

    P: Sequence[Port]
    VCCO = Power()

    def __init__(self):
        self.P = tuple(Port() for _ in range(26))


class X5IOBank(Port):
    """Versal X5IO bank (16 differential pairs + 1 VCCO rail).

    Stanza:

        pcb-bundle x5io-bank :
          port L : diff-pair[16]
          port VCCO : power
    """

    L: Sequence[DiffPair]
    VCCO = Power()

    def __init__(self):
        self.L = tuple(DiffPair() for _ in range(16))


class MIPIPhy(Port):
    """Versal MIPI D-PHY bank (REFCLK + 2 lane pairs + power rails).

    Stanza:

        pcb-bundle mipi-phy :
          port REFCLK : clk-diff-pair
          port RESREF : pin
          port L : lane-pair[2]
          port VCCIO : power
          port VCC : power
    """

    REFCLK = DiffPair()
    RESREF = Port()
    L: Sequence[LanePair]
    VCCIO = Power()
    VCC = Power()

    def __init__(self):
        self.L = tuple(LanePair() for _ in range(2))


class GTRUSB3(Port):
    """Versal GTR/USB3 transceiver bundle.

    Stanza:

        pcb-bundle gtr-usb3 :
          port REFCLK : clk-diff-pair
          port RESREF : pin
          port TX : diff-pair[[0, 3]]
          port TXRX: diff-pair[[1, 2]]
          port VCCIO : power
          port VCC : power

    The stanza `TX : diff-pair[[0, 3]]` syntax declares a sparse-indexed
    array — only indices 0 and 3 exist. We mirror that here with
    `dict[int, DiffPair]` to preserve fidelity to the stanza shape: callers
    must access `usb3.TX[0]` / `usb3.TX[3]`, never `[1]` or `[2]` (those
    indices belong to `TXRX`). The same convention applies to `TXRX`,
    which only has indices `1` and `2`.
    """

    REFCLK = DiffPair()
    RESREF = Port()
    TX: dict[int, DiffPair]
    TXRX: dict[int, DiffPair]
    VCCIO = Power()
    VCC = Power()

    def __init__(self):
        self.TX = {0: DiffPair(), 3: DiffPair()}
        self.TXRX = {1: DiffPair(), 2: DiffPair()}
