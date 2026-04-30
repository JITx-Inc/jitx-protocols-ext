"""Regenerate the pin map of `xc2ve3858_components.py`.

WARNING: this script overwrites the entire `xc2ve3858_components.py` file
with header + landpattern + component class only. It will clobber:

  - The LPDDR5 packing config tables (``_LPDDR5_OPTIMUM_CFG``, etc.)
  - The :py:class:`XC2VE3858Circuit` class (power rails, bundle ports,
    bundle wiring, GPIO Provides, LPDDR5 Provides)
  - The ``_to_x5io_pin_name`` helper

Re-run only when the stanza pin-properties table changes. After running,
re-paste everything below the auto-generated component class from the
previous version.

Usage:
    python _gen/gen_xc2ve3858.py <stanza_path> <output_py_path>
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROW_RE = re.compile(
    r"""^\s*\[\s*
        (?P<pin>[A-Za-z0-9_]+(?:\[\d+\])?)\s*\|\s*
        (?P<pad_row>[A-Z]+)\[(?P<pad_col>\d+)\]\s*\|\s*
        (?P<bank>[^|]+?)\s*\|\s*
        (?P<xbank>[^\]]+?)\s*\]
    """,
    re.VERBOSE,
)

PIN_PARSE = re.compile(r"^(?P<base>[A-Za-z0-9_]+)(?:\[(?P<idx>\d+)\])?$")

HEADER = '''"""Xilinx Versal XC2VE3858 FPGA Component (Pass A: pin map only).

Translation of `components/xc2ve3858.stanza`. This file contains only the
part needed to instantiate the FPGA in the LPDDR5 example:

- 46x46 SSVA2112 BGA landpattern (4 corners cut)
- 2112-pin component with full pad mapping
- Circuit wrapper exposing power rails and a `Provide(LPDDR5)` for the
  X5IO DDR memory controllers

Pass B (deferred — see `xc2ve3858_pass_b_TODO.md`) covers the full Versal
protocol bundle library: gtyp-quad, hdio-bank, pmc-mio-bank, lpd-mio-bank,
mipi-phy, x5io-bank, gtr-usb3 — none of which are required for LPDDR5.

Sources:
- Stanza component: customers/lockheed-martin/tssr-parts/xilinx/components/xc2ve3858.stanza
- Stanza landpattern: customers/lockheed-martin/tssr-parts/xilinx/landpatterns/ssva2112-bga.stanza
- AMD Versal datasheet: https://docs.amd.com/r/en-US/am013-versal-pkg-pinout
"""

from __future__ import annotations

from enum import Enum

from jitx import Net, PadMapping, Provide
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.net import Port
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.grid_planner import CornerCutGridPlanner
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from jitx_protocols_ext.protocols.memory.lpddr5 import LPDDR5, LPDDR5Rank, LPDDR5Width


class SSVA2112BGALandpattern(BGA):
    """Xilinx Versal SSVA2112 — 46x46 BGA, 0.5 mm balls, 0.8 mm pitch.

    Corners are cut (1 ball per corner) per the package outline.
    """

    def __init__(self):
        super().__init__(
            num_rows=46,
            num_cols=46,
            ball_diameter=0.5,
            pitch=0.8,
        )
        self.grid_planner(CornerCutGridPlanner(corner_width=1))
        self.pad_config(SMDPadConfig())
        self.package_body(
            RectanglePackage(
                width=Toleranced.exact(37.5),
                length=Toleranced.exact(37.5),
                height=Toleranced.min_max(3.50, 3.90),
            )
        )
        self.density_level(DensityLevel.C)


class XC2VE3858(Component):
    """AMD/Xilinx Versal XC2VE3858 FPGA — 2112-ball SSVA2112 BGA.

    This Pass-A component declares the full pin map. Protocol bundle
    structure (gtyp/hdio/x5io/mipi) is deferred to Pass B; for the LPDDR5
    example the X5IO bank pins are exposed as flat ports, and the
    `XC2VE3858Circuit` wrapper provides the LPDDR5 interface via `Provide()`.
    """

    reference_prefix = "U"
    mpn = "XC2VE3858"
    manufacturer = "AMD/Xilinx"
    description = "Versal AI Edge Series VE3858 FPGA, 2112-ball SSVA2112 BGA"

'''

CIRCUIT_TAIL_HEAD = '''

class LPDDR5Packing(Enum):
    """LPDDR5 pinout packing style for the XC2VE3858 X5IO DDR controllers.

    Mirrors the stanza enum `components/xc2ve3858/LPDDR5Packing`.
    `OPTIMUM` is the default and recommended choice when routing space allows.
    """

    OPTIMUM = "Optimum"
    PACKED_LEFT = "PackedLeft"
    PACKED_RIGHT = "PackedRight"


# Pin name template helpers — mirror stanza `to-x5io-pin-name`.
_X5IO_MC_LOOKUP: dict[int, tuple[int, int]] = {
    700: (0, 0), 701: (0, 1), 702: (0, 2),
    703: (1, 3), 704: (1, 4), 705: (1, 5),
    710: (2, 0), 711: (2, 1), 712: (2, 2),
    713: (3, 3), 714: (3, 4), 715: (3, 5),
}


def _to_x5io_pin_name(bank: int, lane: int, polarity: str) -> str:
    """Reproduce stanza `to-x5io-pin-name(bank, lane, polarity)` exactly."""
    p = 2 * lane + (1 if polarity == "N" else 0)
    half = bank % 2
    lane_offset = 0 if half == 0 else 16
    lane_str = f"_L{lane + lane_offset}{polarity}"
    xcc = "_XCC" if (lane % 4 == 1) else ""
    gc = "_GC" if (lane == 3) else ""
    octad = lane // 4
    octad_pin = p % 8
    octad_str = f"_H{half}O{octad}P{octad_pin}"
    if bank in _X5IO_MC_LOOKUP:
        mc, mc_pair_idx = _X5IO_MC_LOOKUP[bank]
        mc_p = 32 * mc_pair_idx + p
        mc_str = f"_M{mc}P{mc_p}"
    else:
        mc_str = ""
    return f"IO{lane_str}{xcc}{gc}{octad_str}{mc_str}_{bank}"
'''


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: gen_component.py <stanza_path> <out_path>", file=sys.stderr)
        return 2
    stanza_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    rows = []
    for line in stanza_path.read_text().splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        rows.append(
            (
                m.group("pin"),
                m.group("pad_row"),
                int(m.group("pad_col")),
                m.group("bank"),
            )
        )

    base_to_indices: dict[str, set[int | None]] = defaultdict(set)
    for pin, _, _, _ in rows:
        pm = PIN_PARSE.match(pin)
        assert pm
        base = pm.group("base")
        idx = pm.group("idx")
        base_to_indices[base].add(int(idx) if idx is not None else None)

    decl_lines = []
    for base in sorted(base_to_indices.keys()):
        idxs = base_to_indices[base]
        if idxs == {None}:
            decl_lines.append(f"    {base} = Port()")
        else:
            assert None not in idxs, f"Mixed for {base}: {idxs}"
            n = max(idxs) + 1  # type: ignore[type-var]
            assert idxs == set(range(n)), f"Non-contiguous {base}: {idxs}"
            decl_lines.append(f"    {base} = [Port() for _ in range(%d)]" % n)

    map_lines = []
    last_row = None
    for pin, pad_row, pad_col, _ in rows:
        if pad_row != last_row:
            map_lines.append(f"                # Row {pad_row}")
            last_row = pad_row
        pm = PIN_PARSE.match(pin)
        assert pm
        base = pm.group("base")
        idx = pm.group("idx")
        key = f"{base}[{idx}]" if idx is not None else base
        map_lines.append(f"                {key}: landpattern.{pad_row}[{pad_col}],")

    parts: list[str] = [HEADER]
    parts.append("\n".join(decl_lines))
    parts.append("\n\n")
    parts.append("    landpattern = SSVA2112BGALandpattern()\n")
    parts.append("    symbol = BoxSymbol()\n")
    parts.append("\n")
    parts.append("    mapping = [\n")
    parts.append("        PadMapping(\n")
    parts.append("            {\n")
    parts.append("\n".join(map_lines))
    parts.append("\n            }\n")
    parts.append("        )\n")
    parts.append("    ]\n")
    parts.append(CIRCUIT_TAIL_HEAD)

    out_path.write_text("".join(parts))
    print(f"Wrote {out_path} ({len(rows)} pins, {len(decl_lines)} bases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
