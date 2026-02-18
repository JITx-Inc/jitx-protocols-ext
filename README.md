# jitx-protocols-ext

JITX protocol bundles, signal integrity constraints, and example designs for high-speed interfaces.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Protocols](#protocols)
  - [Memory Protocols](#memory-protocols)
  - [High-Speed Serial Protocols](#high-speed-serial-protocols)
- [Protocol Examples](#protocol-examples)
  - [Memory Examples](#memory-examples)
  - [Serial Examples](#serial-examples)
- [Common Infrastructure](#common-infrastructure)
- [Development](#development)

---

## Overview

This library provides:

1. **Protocol Bundles**: Port definitions for memory interfaces (DDR4, LPDDR4, LPDDR5, GDDR7) and high-speed serial interfaces (JESD204, PCIe, SATA, SFP/QSFP)

2. **Signal Integrity Constraints**: Timing skew, insertion loss, and impedance constraints that can be applied to protocol connections

3. **Example Designs**: Complete working examples showing controller-to-memory and device-to-device connections with SI constraints

## Installation

```bash
# Install the package
pip install .

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Build all designs
python -m jitx build-all

# Run tests
hatch test

# Format and lint
hatch fmt
```

---

## Protocols

### Memory Protocols

#### DDR4 (`protocols/memory/ddr4.py`)

DDR4 SDRAM interface supporting x16 width with single or dual rank configurations.

**Bundle Structure:**
```
DDR4
├── data: DDR4Data
│   ├── DQ[16]         - 16-bit data bus
│   ├── DQS[2]         - Data strobes (DiffPair per byte lane)
│   └── DM_n[2]        - Data masks
└── acc: DDR4ACC
    ├── A[17]          - Address bus
    ├── BA[2]          - Bank address
    ├── BG[2]          - Bank group
    ├── CK[2]          - Clock (DiffPair per chip)
    ├── CKE[1-2]       - Clock enable
    ├── CS_n[1-2]      - Chip select
    ├── ODT[1-2]       - On-die termination
    ├── ACT_n          - Activate
    ├── RESET_n        - Reset
    ├── PAR            - Parity
    └── ALERT_n        - Alert
```

**Constraint Parameters (`DDR4ConstraintParams`):**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `skew_ck` | ±2.5ps | CK intra-pair skew |
| `skew_dqs` | ±2.5ps | DQS intra-pair skew |
| `skew_ck_dqs` | -300ps to +500ps | CK to DQS timing |
| `skew_dqs_dq` | ±10ps | DQS to DQ/DM skew |
| `loss` | 5.0dB | Maximum insertion loss |

#### LPDDR4 (`protocols/memory/lpddr4.py`)

Low-power DDR4 for mobile applications. Supports x16, x32, and x64 widths with 1-3 ranks.

**Bundle Structure:**
```
LPDDR4
└── ch[1-4]: LPDDR4_X16      - x16 channels
    ├── d[2]: LPDDR4Lane     - Byte lanes
    │   ├── dq[8]            - Data bits
    │   ├── dqs (DiffPair)   - Data strobe
    │   └── dmi              - Data mask/inversion
    ├── ck (DiffPair)        - Clock
    ├── cke[ranks]           - Clock enable
    ├── cs[ranks]            - Chip select
    └── ca[6]                - Command/address
```

**Constraint Parameters (`LPDDR4ConstraintParams`):**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `skew_ck` | ±2.0ps | CK intra-pair skew |
| `skew_ck_cke` | ±8.0ps | CK to CKE skew |
| `skew_ck_cs` | ±8.0ps | CK to CS skew |
| `skew_ck_ca` | ±8.0ps | CK to CA skew |
| `skew_ck_dqs` | -500ps to +2500ps | CK to DQS skew |
| `skew_dqs` | ±2.0ps | DQS intra-pair skew |
| `skew_dqs_dq` | ±5.0ps | DQS to DQ/DMI skew |
| `loss` | 5.0dB | Maximum insertion loss |

#### LPDDR5 (`protocols/memory/lpddr5.py`)

LPDDR5/LPDDR5X for high-bandwidth mobile applications. Supports x32 and x64 widths.

**Key Differences from LPDDR4:**
- Separate Write Clock (WCK) and Read Data Strobe (RDQS)
- 7-bit Command/Address bus
- Tighter timing constraints

**Bundle Structure:**
```
LPDDR5
├── d[channels][2]: LPDDR5DataLane
│   ├── dq[8]              - Data bits
│   ├── wck (DiffPair)     - Write clock
│   ├── rdqs (DiffPair)    - Read data strobe
│   └── dmi                - Data mask/inversion
├── cs[channels][ranks]    - Chip selects
├── ck[channels] (DiffPair) - Clocks
├── ca[channels][7]        - Command/address
└── reset_n                - Shared reset
```

#### GDDR7 (`protocols/memory/gddr7.py`)

Graphics DDR7 for high-performance GPU memory. Fixed 4-channel architecture.

**Bundle Structure:**
```
GDDR7
├── data[4]: GDDR7DataChannel
│   ├── DQ[10]             - 10-bit data (PAM3/NRZ)
│   ├── RCK (DiffPair)     - Read clock
│   ├── WCK (DiffPair)     - Write clock
│   ├── CA[5]              - Command/address
│   ├── DQE                - Error detection
│   └── ERR                - Error flag
└── control: GDDR7ControlChannel
    ├── RESET_n            - Reset
    ├── ZQ_AB              - Impedance cal (A/B)
    └── ZQ_CD              - Impedance cal (C/D)
```

**Constraint Parameters (`GDDR7ConstraintParams`):**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `skew_rck` | ±10fs | RCK intra-pair skew |
| `skew_wck` | ±10fs | WCK intra-pair skew |
| `skew_rck_wck` | ±20ps | RCK to WCK skew |
| `skew_dq_dqe` | ±5ps | DQ to DQE skew |
| `loss` | 5.0dB | Maximum insertion loss |

---

### High-Speed Serial Protocols

#### JESD204 (`protocols/jesd204.py`)

JESD204B/C interface for high-speed data converters (ADC/DAC to FPGA/ASIC).

**Bundle Structure:**
```
JESD204
├── lane[1-32] (DiffPair)    - Unidirectional CML data lanes
├── SYNC (DiffPair, optional) - Sync signal (LVDS, receiver → transmitter)
├── SYSREF (DiffPair, optional) - System reference (Subclass 1)
└── DEVCLK (DiffPair, optional) - Device clock
```

**Key Differences from PCIe/SATA:**
- Data lanes are **unidirectional** (each is a single `DiffPair`, not a `LanePair`)
- **DC-coupled** CML signaling (no AC coupling capacitors needed)
- SYNC~ flows in the opposite direction from data

**Versions:**
| Version | Max Lane Rate | Encoding | SYNC~ Required |
|---------|---------------|----------|----------------|
| JESD204B | 12.5 Gbps | 8B/10B | Yes |
| JESD204C | 32.5 Gbps | 64B/66B | No (embedded) |

**Constraint Parameters (`JESD204Standard`):**
| Parameter | JESD204B | JESD204C | Description |
|-----------|----------|----------|-------------|
| `skew` | ±1.0ps | ±0.5ps | Intra-pair skew |
| `lane_skew` | ±100ps | ±50ps | Inter-lane skew |
| `loss` | 12.0dB | 15.0dB | Maximum insertion loss |
| `impedance` | 100Ω ±20% | 100Ω ±15% | Differential impedance |

#### PCIe (`protocols/pcie.py`)

PCI Express supporting Gen1 through Gen6, x1 through x16 widths.

**Bundle Structure:**
```
PCIe
├── data: PCIeData
│   └── lane[width]: PCIeLane
│       ├── TX (DiffPair)  - Transmit pair
│       └── RX (DiffPair)  - Receive pair
└── ctrl: PCIeControl (optional)
    ├── REFCLK (DiffPair)  - Reference clock
    ├── PERST_n            - Reset
    ├── CLKREQ_n           - Clock request
    ├── WAKE_n             - Wake
    └── PRSNT              - Presence detect
```

**Usage Modes:**
- `xover=False` (default): Straight-through (TX→TX, RX→RX) for card-edge connectors
- `xover=True`: Crossover (TX→RX, RX→TX) for IC-to-IC connections

**Helper Function:**
```python
connect_pcie_null_modem(a: PCIe, b: PCIe) -> list
```
Creates crossover topology connections for null-modem (IC-to-IC) configurations.

#### SATA (`protocols/sata.py`)

Serial ATA interface for storage devices.

**Bundle Structure:**
```
SATA
└── lane: SATALane
    ├── TX (DiffPair)      - Transmit pair
    └── RX (DiffPair)      - Receive pair
```

**Constraint Notes:**
- Always uses crossover topology (TX→RX)
- 100Ω differential impedance
- Insertion loss ≤5.0dB

#### SFP/QSFP (`protocols/sfp.py`)

Small Form-factor Pluggable interfaces for optical/copper networking.

**Variants:**
| Type | Lanes | Description |
|------|-------|-------------|
| `SFP` | 1 | Standard SFP/SFP+ |
| `SFP_DD` | 2 | SFP Double Density |
| `QSFP` | 4 | Quad SFP |
| `QSFP_DD` | 8 | QSFP Double Density |

**Bundle Structure:**
```
SFP_Lane (base for all variants)
└── lanes[n]: SFPLink
    ├── TX (DiffPair)      - Transmit pair
    └── RX (DiffPair)      - Receive pair
```

---

## Protocol Examples

All examples are in `jitx_protocols_ext/examples/protocols/` and demonstrate:
- Component definition with landpatterns and pad mappings
- Memory/controller circuits with direct ports or Provide() patterns
- Topology connections using `>>` for SI constraint propagation
- Application of protocol-specific constraints

### Memory Examples

#### DDR4 Example (`examples/protocols/memory/ddr4_example.py`)

Demonstrates DDR4 x16 fly-by topology with two Micron MT40A1G16TB memory chips.

**Components:**
- `MT40A1G16TB_062E_F`: Real Micron DDR4 memory with FBGA96 split-BGA landpattern
- `DDR4ControllerComponent2`: Generic controller with Provide() pattern

**Key Features:**
- Split-BGA landpattern generator for DDR4 package
- Fly-by topology: `io.DQ → mem0.DQ → mem1.DQ`
- Per-chip clock and control signals

#### LPDDR4 Example (`examples/protocols/memory/lpddr4_example.py`)

Samsung K4FBE3D4HB-KHCL x32 dual-rank memory connected to controller.

**Components:**
- `K4FBE3D4HB_KHCL`: Samsung LPDDR4 memory (22x12 BGA)
- `LPDDR4ControllerComponent`: Controller with Provide() pattern

**Key Features:**
- Dual x16 channels (A and B)
- Dual rank support with per-rank CKE/CS

#### LPDDR5 Example (`examples/protocols/memory/lpddr5_example.py`)

Micron MT62F4G32D8DV-026_AIT_B LPDDR5X memory (automotive grade).

**Components:**
- `MT62F4G32D8DV_026_AIT_B`: 16GB LPDDR5X (315-ball LFBGA)
- `LPDDR5ControllerCircuit`: Controller with Provide() pattern

**Key Features:**
- x32 DualRank configuration
- Separate WCK and RDQS per lane
- 7-bit CA bus per channel

#### GDDR7 Example (`examples/protocols/memory/gddr7_example.py`)

GPU IC to GDDR7 memory connection with 4-channel interface.

**Components:**
- `GDDR7MemoryComponent`: FBGA266 split-BGA memory
- `GDDR7ICComponent`: 30x30 BGA GPU/IC with checkerboard ground pattern

**Key Features:**
- 4 data channels with 10-bit PAM3 data
- RCK/WCK clock pairs per channel
- Checkerboard signal/ground ball pattern for IC

### Serial Examples

#### JESD204 Example (`examples/protocols/jesd204/jesd204_example.py`)

4-lane JESD204B ADC-to-FPGA connection with SI constraints.

**Components:**
- `JESD204ADCComponent`: Dummy quad-channel ADC with 4 serial output lanes
- `JESD204FPGAComponent`: Dummy FPGA with 4 serial input lanes

**Features:**
- Unidirectional data lanes (ADC TX → FPGA RX)
- DC-coupled CML (no blocking capacitors)
- SYNC~ routed from FPGA back to ADC
- SYSREF and DEVCLK clock routing

#### PCIe Example (`examples/protocols/pcie/pcie_example.py`)

PCIe Gen3 x2 with AC coupling and null-modem topology.

**Features:**
- `DiffPairCoupler`: AC coupling circuit using blocking caps
- Card-edge mode (straight-through) and IC-to-IC mode (crossover)
- `connect_pcie_null_modem()` helper for null-modem connections

#### SATA Example (`examples/protocols/sata/sata_example.py`)

SATA host-to-device and IC-to-IC connections.

**Features:**
- TX→RX crossover topology
- AC coupling with blocking capacitors

#### SFP Example (`examples/protocols/sfp/sfp_example.py`)

Single-lane SFP and 4-lane QSFP connections.

**Features:**
- TX→RX crossover topology (optical-style)
- AC coupling on TX paths

---

## Common Infrastructure

### Board and Stackup (`common/example_board.py`)

Provides a 6-layer PCB stackup suitable for high-speed designs.

**Stackup:**
```
Top Soldermask (13µm)
Layer 0 - Signal (30µm Cu)
Prepreg (60µm)
Layer 1 - Inner (25µm Cu)
Prepreg (60µm)
Layer 2 - Signal (15µm Cu)
Core (70µm FR4)
Layer 3 - Signal (25µm Cu)
Prepreg (60µm)
Layer 4 - Inner (25µm Cu)
Prepreg (60µm)
Layer 5 - Signal (30µm Cu)
Bottom Soldermask (13µm)
```

**Routing Structures:**
| Structure | Impedance | Use Case |
|-----------|-----------|----------|
| `SE40RoutingStructure` | 40Ω | LPDDR4 |
| `SE45RoutingStructure` | 45Ω | DDR4 |
| `SE50RoutingStructure` | 50Ω | General SE |
| `diff_85` | 85Ω diff | LPDDR4 CK/DQS |
| `diff_90` | 90Ω diff | DDR4 CK/DQS |
| `diff_100` | 100Ω diff | PCIe, SATA, SFP |

**Via Definitions:**
- `MicroViaTop1-4`: Laser-drilled microvias to inner layers
- `DefaultTHVia`: Mechanical through-hole via

### Example Components (`common/example_components.py`)

Components with pin models for SI topology propagation.

**`BlockingCapacitor`:**
- 0201 package blocking capacitor for AC coupling
- `BridgingPinModel` allows SI constraints to propagate through

**`PullUpResistor`:**
- 0201 package pull-up resistor
- `BridgingPinModel` for SI propagation

---

## Development

### Commands

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

# Build distributable wheel/sdist
hatch build
```

### Project Structure

```
jitx_protocols_ext/
├── protocols/                 # Protocol bundle definitions
│   ├── memory/
│   │   ├── ddr4.py           # DDR4 bundle + constraints
│   │   ├── lpddr4.py         # LPDDR4 bundle + constraints
│   │   ├── lpddr5.py         # LPDDR5 bundle + constraints
│   │   └── gddr7.py          # GDDR7 bundle + constraints
│   ├── jesd204.py            # JESD204B/C bundle + constraints
│   ├── pcie.py               # PCIe bundle + constraints
│   ├── sata.py               # SATA bundle + constraints
│   └── sfp.py                # SFP/QSFP bundle + constraints
├── examples/protocols/        # Example designs
│   ├── jesd204/
│   ├── memory/
│   ├── pcie/
│   ├── sata/
│   └── sfp/
├── common/                    # Shared infrastructure
│   ├── example_board.py      # Board, stackup, vias
│   └── example_components.py # Blocking caps, pull-ups
tests/                         # Test suite
├── test_imports.py
└── test_jesd204.py
```

### Key Patterns

**Topology Connections:**
Use `>>` operator to preserve topology for SI constraints:
```python
# Correct - preserves topology
self.topos.append(self.io.dq[i] >> self.mem.DQ[i])

# Incorrect - loses topology information
self.nets.append(self.io.dq[i] + self.mem.DQ[i])
```

**Direct Port vs Provide:**
- **Memory components**: Use direct ports (`io = LPDDR5(...)`) for fixed pin assignments
- **Controller components**: Use `Provide()` for flexible pin assignment

**Crossover Topology:**
For SFP/SATA/PCIe IC-to-IC connections:
```python
# TX from source connects to RX on destination
topos.append(src.lane.TX >> dst.lane.RX)
topos.append(dst.lane.TX >> src.lane.RX)
```

---

## License

See LICENSE file for details.
