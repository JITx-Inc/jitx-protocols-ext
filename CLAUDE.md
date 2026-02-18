# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation

- **Official docs**: https://docs.jitx.com
- **LLM-optimized docs**: https://docs.jitx.com/llms.txt (fetch this for API/syntax questions)

## Overview

This is `jitx-protocols-ext`, a JITX protocol extension library. It provides:

- **Protocol bundles** - Signal definitions for JESD204B/C, PCIe, SATA, SFP/QSFP, DDR4, LPDDR4, LPDDR5, GDDR7
- **Signal integrity constraints** - Timing skew, insertion loss, and impedance constraints
- **Example designs** - Complete working examples with component definitions and SI-constrained topologies

## Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
hatch test

# Run tests with coverage
hatch test cov

# Lint and format
hatch run lint:check
hatch run lint:fmt

# Type checking
hatch run types:check

# Build all JITX designs
python -m jitx build-all

# Build distributable package
hatch build
```

## Architecture

### Protocol Bundles (`jitx_protocols_ext/protocols/`)

Protocol bundles define signal groupings for standard interfaces:

- **JESD204** (`jesd204.py`): JESD204B/C with unidirectional DiffPair data lanes, SYNC~, SYSREF, DEVCLK
- **Memory** (`memory/`): DDR4, LPDDR4, LPDDR5, GDDR7 interfaces
- **High-speed serial**: PCIe, SATA, SFP/QSFP

Bundles inherit from `Port` and compose `DiffPair`, `LanePair`, `Power` from `jitx.common`.

### Examples (`jitx_protocols_ext/examples/protocols/`)

Complete working examples with dummy components, Provide() pin assignment, and SI-constrained topologies for each protocol.

### Common Infrastructure (`jitx_protocols_ext/common/`)

Shared board/stackup definitions and example components (blocking capacitors, pull-up resistors) with pin models for SI propagation.

## Key Dependencies

- `jitx>=4.0.0,<5` - Core JITX Python API
- `jitxlib-standard>=4.0.0,<5` - Standard library (landpatterns, symbols)
- `jitxlib-parts>=1.0.0,<2` - Component part definitions
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
