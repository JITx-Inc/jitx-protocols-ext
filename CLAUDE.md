# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation

- **Official docs**: https://docs.jitx.com
- **LLM-optimized docs**: https://docs.jitx.com/llms.txt (fetch this for API/syntax questions)

## Overview

This is `jitxlib-standard`, the JITX Standard Library for Python. It provides reusable building blocks for electronic circuit design including:

- **Landpattern generators** - Framework for generating component footprints (BGA, QFN, SOIC, SOT, SOP, SON, etc.)
- **Symbol generators** - Schematic symbols for resistors, capacitors, inductors, logic gates, op-amps, transformers
- **Protocol bundles** - Signal definitions for USB, Ethernet (MII/RGMII/GMII), DisplayPort, SATA, PCIe, SFP, DDR4/LPDDR4/LPDDR5/GDDR7
- **Via structures** - Single-ended and differential via structures with ground cages and antipads
- **Circuit utilities** - CircuitPool for aggregating provides across multiple circuit instances

## Development Commands

```bash
# Run tests with coverage
hatch test --cover

# Run tests for specific Python version
hatch test --python 3.12
hatch test --python 3.13

# Run a single test file
hatch test tests/test_landpattern_gen.py

# Run a single test method
hatch test tests/test_landpattern_gen.py::LandpatternGeneratorTestCase::test_initialize_directly

# Format and lint (ruff)
hatch fmt

# Check formatting without changes
hatch fmt --check

# Type checking (pyright)
hatch run types:check
hatch run types:stats

# Build
hatch build
```

## Architecture

### Landpattern Generator Framework (`src/jitxlib/landpatterns/`)

The landpattern system uses a mixin-based architecture with lazy evaluation:

1. **`LandpatternGenerator`** - Base class that extends `jitx.Landpattern` with automatic rebuild on attribute access
2. **`LandpatternProvider`** - Mixin providing `_build()` and `_build_decorate()` hooks; subclasses must call `super()._build()` to maintain the build chain
3. **Generator Mixins** - Add functionality via method chaining:
   - `DualColumn`, `QuadColumn` - Pad layouts
   - `SilkscreenOutline`, `Pad1Marker`, `ReferenceDesignatorMixin` - Decorations
   - `ThermalPadGeneratorMixin` - Thermal pad generation
   - `ExcessCourtyard` - Courtyard calculations

Example composition pattern:
```python
class MyLandpattern(
    A1,                        # Numbering starts at A1
    AlphaDictNumbering,        # Alpha row, numeric column naming
    Pad1Marker,                # Pin 1 indicator
    ExcessCourtyard,           # Courtyard sizing
    SilkscreenOutline,         # Outline generation
    DualColumn,                # 2-column pad layout (must be last)
):
    def __base_init__(self):
        super().__base_init__()
        self.pad_config(SMDPadConfig())
        self.silkscreen_outline(SoldermaskBased())
```

### Protocol Bundles (`src/jitxlib/protocols/`)

Protocol bundles define signal groupings for standard interfaces:

- **USB** (`usb.py`): `USB2`, `USBSuperSpeed`, `USB_C` with transport vs connector distinction
- **Ethernet** (`ethernet/`): MII variants (MII, RMII, RGMII, GMII) and MDI (100BASE-TX, 1000BASE-T, 10GBASE-KR)
- **Memory** (`memory/`): DDR4, LPDDR4, LPDDR5, GDDR7 interfaces
- **High-speed serial**: PCIe, SATA, SFP, DisplayPort

Bundles inherit from `Port` and compose `DiffPair`, `LanePair`, `Power` from `jitx.common`.

### Via Structures (`src/jitxlib/via_structures/`)

Via structures are `Circuit` subclasses for SI-aware via transitions:

- **`SingleViaStructure`** - Single-ended signals with `sig_in`, `sig_out`, `COMMON` ports
- **`DifferentialViaStructure`** - Differential pairs with configurable pitch
- **`ViaGroundCage`** / **`PolarViaGroundCage`** - Ground via patterns
- **`AntiPad`** / **`SimpleAntiPad`** - Keepout regions on specified layers

### CircuitPool (`src/jitxlib/circuits/pool.py`)

Aggregates `Provide` ports from multiple circuit instances into a single pool, enabling unified pin assignment across partitioned circuits.

## Testing Patterns

Tests use `SampleDesign` with `@inline` circuits:
```python
class MyTestDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        component = MyComponent()
```

Use `SubstrateContext(SampleSubstrate())` when testing landpatterns directly.

## Key Dependencies

- `jitx>=4.0.0,<4.1` - Core JITX Python API
- Python 3.12+ required

---

## JITX Python Development Rules

### Golden Rules

1. **ALWAYS** inspect component source + docstring before importing/instantiating/connecting
2. **ALWAYS** check Python language server feedback and fix issues
3. **ALWAYS** run `python -m jitx build-all` to verify designs (never `python main.py`)
4. **NEVER** use `=` for electrical connections; use `+` or `+=`
5. **NEVER** add comments that duplicate information already in the code

### Net Connections

```python
# ❌ Wrong (assignment, no electrical connection)
self.vcc = self.battery.p[1]

# ✅ Correct (use += to add to existing net)
self.vcc += self.battery.p[1]

# ✅ Correct (use + to create new net)
self.power_net = self.vcc + self.battery.p[1]

# ✅ High-speed topology connections (use >>)
self.usb_topo = self.usb.data.p >> self.mcu.USB_DP
```

**When to use each:**
- `+=` - Adding to an existing net
- `+` - Creating a new net connecting multiple points
- `>>` - High-speed nets that will be part of a topology (USB, PCIe, etc.)

### Port Types

Use specialized types from `jitx.common` instead of generic `Port()`:

```python
from jitx.common import Power, GPIO, DiffPair, LanePair

power = Power()      # .Vp, .Vn
gpio = GPIO()        # .gpio
diff = DiffPair()    # .P, .N
```

Protocol bundles from `jitxlib.protocols`: `USB2()`, `USB_C()`, `USBSuperSpeed()`, etc.

Use generic `Port()` only for non-standard signals (custom enables, sensor outputs).

### Port Definitions

Ports must be class attributes, not defined in `__init__`:

```python
class MyCircuit(Circuit):
    power = Power()           # ✅ Class attribute
    input_signal = Port()     # ✅ Class attribute
```

### Component Instantiation

Components can be class attributes or instantiated in `__init__`:

```python
class MyCircuit(Circuit):
    gate = SN74LVC1G04()  # Class attribute (simple case)

    def __init__(self, count: int):
        self.gates = [SN74LVC1G04() for _ in range(count)]  # In __init__ (parameterized)
```

### Resistors and Capacitors

```python
from jitxlib.parts import Resistor, Capacitor

# Direct instantiation
self.r = Resistor(resistance=10e3)
self.c = Capacitor(capacitance=100e-9)

# Using .insert() for bypass caps (preferred)
self.bypass = Capacitor(capacitance=100e-9).insert(vcc, gnd, short_trace=True)
self.sense = Resistor(resistance=0.1).insert(battery_pos, vcc)
```

Use `short_trace=True` for bypass caps to minimize trace length to power pins.

### Require Pattern

Use `require()` as a local variable, not instance attribute:

```python
# ❌ Wrong
self.eth_mdi = self.ethernet_jack.require(MDI1000BaseT)

# ✅ Correct
eth_mdi = self.ethernet_jack.require(MDI1000BaseT)
self.net = eth_mdi.TP[0].n + eth_mdi.TP[1].n
```

### Power/Ground Symbols

Add symbols for named power and ground nets:

```python
from jitx import Net
from jitxlib.symbols.net_symbols import GroundSymbol, PowerSymbol

self.gnd = Net(name="GND")
self.vcc = Net(name="VCC")
self.gnd.symbol = GroundSymbol()
self.vcc.symbol = PowerSymbol()
```

### Pours

```python
from jitx import Pour, current

self.gnd += Pour(layer=0, shape=current.design.board.shape, isolate=0.1)
self.gnd += Pour(layer=1, shape=current.design.board.shape, isolate=0.1)
```

### Common Import Pattern

```python
from jitx import Board, Circle, LayerSet, Net, Port, Pour, Side, current
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.feature import KeepOut, Soldermask
from jitx.shapes.composites import rectangle
from jitxlib.parts import Capacitor, Resistor
from jitxlib.symbols.net_symbols import GroundSymbol, PowerSymbol
```

### DRY Coding

Use lists and loops instead of repetition:

```python
self.esd_resistors = []
for poke, cap_port in zip(self.pokes, self.driver.cap):
    self.gnd += poke.B
    esd_resistor = Resistor(resistance=1e3).insert(poke.A, cap_port)
    self.esd_resistors.append(esd_resistor)
```

### Critical Gotchas

- Use `+` for electrical connections, **never** `=`
- Define **ports as class attributes**, not in `__init__`
- Run `python -m jitx build-all`, not `python file.py`
- Provide **both** SymbolMapping and PadMapping when defining custom components
- Don't create subclasses for landpatterns/symbols when existing classes work
