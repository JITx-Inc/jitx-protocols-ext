"""Generic FR-4 Board and Stackup for Protocol Examples.

Translation of jsl/examples/protocols/common/example-board.stanza.

A baseline 6-layer FR-4 stackup with single-ended (40/45/50 Ω) and
differential (85/90/100 Ω) routing structures. Used by the PCIe, USB,
DDR4, GDDR7, LPDDR4, LPDDR5 (generic), JESD204, SATA, and SFP examples.

For an HDI-class higher-performance option (8-layer symmetric, low-loss
generic dielectric, BGA-grade fab rules), see
:py:mod:`examples.common.high_perf_board`. The XC2VE3858 + LPDDR5 example
is wired to that board by default.
"""

from jitx.board import Board
from jitx.layerindex import Side
from jitx.shapes.composites import rectangle
from jitx.si import DifferentialRoutingStructure, PinModel, RoutingStructure
from jitx.stackup import Conductor, Dielectric, Stackup
from jitx.substrate import FabricationConstraints, Substrate
from jitx.toleranced import Toleranced
from jitx.via import Via, ViaType
from jitx.shapes.shapely import ShapelyGeometry

# Materials
class Copper(Conductor):
    """Copper conductor material"""

    roughness = 0.001  # 1um roughness


class FR4Core(Dielectric):
    """FR4 Core dielectric material"""

    dielectric_coefficient = 3.6
    loss_tangent = 0.02


class Soldermask(Dielectric):
    """Soldermask dielectric material (Taiyo BSN4000)"""

    dielectric_coefficient = 3.7
    loss_tangent = 0.02


class FR4Prepreg(Dielectric):
    """FR4 Prepreg dielectric material"""

    dielectric_coefficient = 3.5
    loss_tangent = 0.02


class ExampleStackup(Stackup):
    """6-Layer Stackup for High-Speed Protocol Examples

    Translation of example-stackup from example-board.stanza.
    Total thickness: ~0.826mm (0.032 inches)
    """

    # Top surface
    top_soldermask = Soldermask(thickness=0.013)
    # Signal layers and dielectrics (top to bottom)
    layer0 = Copper(thickness=0.030)  # Top signal
    prepreg1 = FR4Prepreg(thickness=0.060)
    layer1 = Copper(thickness=0.025)  # Inner signal/ground
    prepreg2 = FR4Prepreg(thickness=0.060)
    layer2 = Copper(thickness=0.015)  # Signal
    core = FR4Core(thickness=0.070)  # Core
    layer3 = Copper(thickness=0.025)  # Signal
    prepreg3 = FR4Prepreg(thickness=0.060)
    layer4 = Copper(thickness=0.025)  # Inner signal/power
    prepreg4 = FR4Prepreg(thickness=0.060)
    layer5 = Copper(thickness=0.030)  # Bottom signal
    # Bottom surface
    bottom_soldermask = Soldermask(thickness=0.013)


# Routing Structures
class SE40RoutingStructure(RoutingStructure):
    """40 Ohm single-ended routing structure (for LPDDR4)"""

    def __init__(self):
        outer_layer = RoutingStructure.Layer(
            trace_width=0.14,
            clearance=0.10,
            velocity=0.19e12,
            insertion_loss=0.008,
            neck_down=RoutingStructure.NeckDown(trace_width=0.18, clearance=0.1),
        )

        mid_layer = RoutingStructure.Layer(
            trace_width=0.15,
            clearance=0.11,
            velocity=0.19e12,
            insertion_loss=0.008,
            neck_down=RoutingStructure.NeckDown(trace_width=0.18, clearance=0.1),
        )

        super().__init__(
            layers={
                0: outer_layer, 1: mid_layer, 2: mid_layer,
                -3: mid_layer, -2: mid_layer, -1: outer_layer,
            },
            impedance=40.0,
        )


class SE45RoutingStructure(RoutingStructure):
    """45 Ohm single-ended routing structure (for DDR4)"""

    def __init__(self):
        outer_layer = RoutingStructure.Layer(
            trace_width=0.12,
            clearance=0.10,
            velocity=0.19e12,
            insertion_loss=0.008,
            neck_down=RoutingStructure.NeckDown(trace_width=0.17, clearance=0.1),
        )

        mid_layer = RoutingStructure.Layer(
            trace_width=0.13,
            clearance=0.11,
            velocity=0.19e12,
            insertion_loss=0.008,
            neck_down=RoutingStructure.NeckDown(trace_width=0.17, clearance=0.1),
        )

        super().__init__(
            layers={
                0: outer_layer, 1: mid_layer, 2: mid_layer,
                -3: mid_layer, -2: mid_layer, -1: outer_layer,
            },
            impedance=45.0,
        )


class SE50RoutingStructure(RoutingStructure):
    """50 Ohm single-ended routing structure"""

    def __init__(self):
        outer_layer = RoutingStructure.Layer(
            trace_width=0.10,
            clearance=0.10,
            velocity=0.19e12,
            insertion_loss=0.008,
            neck_down=RoutingStructure.NeckDown(trace_width=0.156, clearance=0.1),
        )

        mid_layer = RoutingStructure.Layer(
            trace_width=0.11,
            clearance=0.11,
            velocity=0.19e12,
            insertion_loss=0.008,
            neck_down=RoutingStructure.NeckDown(trace_width=0.156, clearance=0.1),
        )

        super().__init__(
            layers={
                0: outer_layer, 1: mid_layer, 2: mid_layer,
                -3: mid_layer, -2: mid_layer, -1: outer_layer,
            },
            impedance=50.0,
        )


def create_differential_routing_structure(
    impedance: Toleranced,
) -> DifferentialRoutingStructure:
    """Create a differential routing structure for a given impedance

    Args:
        impedance: Target differential impedance (75, 85, 90, or 100 Ohm)

    Returns:
        DifferentialRoutingStructure instance configured for the impedance
    """
    # Get typical value from Toleranced
    ti = impedance.typ

    # Determine trace width based on impedance. 75 Ω is the LPDDR5 target
    # per AMD UG863; trace width interpolated below the 85 Ω entry.
    if ti == 75.0:
        tw = 0.1100
    elif ti == 85.0:
        tw = 0.1200
    elif ti == 90.0:
        tw = 0.1275
    elif ti == 100.0:
        tw = 0.1310
    else:
        raise ValueError(
            f"Unsupported impedance: {ti}. Must be 75, 85, 90, or 100 Ohm"
        )

    outer_layer = DifferentialRoutingStructure.Layer(
        trace_width=tw,
        pair_spacing=tw / 1.2,
        clearance=0.150,
        velocity=0.19e12,
        insertion_loss=0.008,
    )

    mid_layer = DifferentialRoutingStructure.Layer(
        trace_width=tw,
        pair_spacing=2.0 * tw,
        clearance=0.300,
        velocity=0.19e12,
        insertion_loss=0.008,
    )

    return DifferentialRoutingStructure(
        layers={
            0: outer_layer, 1: mid_layer, 2: mid_layer,
            -3: mid_layer, -2: mid_layer, -1: outer_layer,
        },
        uncoupled_region=SE50RoutingStructure(),
        impedance=ti,
    )


class ExampleFabConstraints(FabricationConstraints):
    """Fabrication constraints for the example substrate"""

    min_copper_width = 0.075
    min_copper_copper_space = 0.075
    min_copper_hole_space = 0.075
    min_copper_edge_space = 0.254
    min_annular_ring = 0.050
    min_drill_diameter = 0.100
    min_silkscreen_width = 0.100
    min_pitch_leaded = 0.350
    min_pitch_bga = 0.350
    max_board_width = 406.4
    max_board_height = 558.8
    min_silk_solder_mask_space = 0.050
    min_silkscreen_text_height = 0.380
    solder_mask_registration = 0.050
    min_th_pad_expand_outer = 0.050
    min_soldermask_opening = 0.152
    min_soldermask_bridge = 0.102
    min_hole_to_hole = 0.100
    min_pth_pin_solder_clearance = 0.500


class ExampleSubstrate(Substrate):
    """6-Layer Substrate for High-Speed Protocol Examples"""

    stackup = ExampleStackup()
    constraints = ExampleFabConstraints()
    # Single-ended routing structures
    se_40 = SE40RoutingStructure()
    se_45 = SE45RoutingStructure()
    se_50 = SE50RoutingStructure()
    # Differential routing structures for common impedances
    diff_75 = create_differential_routing_structure(Toleranced.percent(75, 10))
    diff_85 = create_differential_routing_structure(Toleranced.percent(85, 5))
    diff_90 = create_differential_routing_structure(Toleranced.percent(90, 5))
    diff_100 = create_differential_routing_structure(Toleranced.percent(100, 5))


    # Via definitions
    class MicroViaTop1(Via):
        start_layer = Side.Top
        stop_layer = 1
        diameter = 0.200
        hole_diameter = 0.100
        type = ViaType.LaserDrill
        models = {(0,1):PinModel(0.1e-15, 0.0)}


    class MicroViaTop2(Via):
        start_layer = Side.Top
        stop_layer = 2
        diameter = 0.200
        hole_diameter = 0.100
        type = ViaType.LaserDrill
        models = {(0,2):PinModel(0.2e-15, 0.0)}


    class MicroViaTop3(Via):
        start_layer = Side.Top
        stop_layer = 3
        diameter = 0.200
        hole_diameter = 0.100
        type = ViaType.LaserDrill
        models = {(0,3):PinModel(0.3e-15, 0.0)}


    class MicroViaTop4(Via):
        start_layer = Side.Top
        stop_layer = 4
        diameter = 0.200
        hole_diameter = 0.100
        type = ViaType.LaserDrill
        models = {(0,4):PinModel(0.4e-15, 0.0)}


    class DefaultTHVia(Via):
        start_layer = Side.Top
        stop_layer = Side.Bottom
        diameter = 0.275
        hole_diameter = 0.150
        type = ViaType.MechanicalDrill
        models = {(0,5):PinModel(0.5e-15, 0.0)}


# Board shape: 50mm x 30mm
board_shape = rectangle(50.0, 30.0)
bs = ShapelyGeometry.from_shape(rectangle(50.0, 30.0))
signal_shape = bs.buffer(-0.5)

class ExampleBoard(Board):
    """Board Definition for Protocol Examples

    Translation of an-example-board from example-board.stanza.
    """

    shape = board_shape
    signal_area = board_shape
    substrate = ExampleSubstrate
    vias = [
        ExampleSubstrate.MicroViaTop1,
        ExampleSubstrate.MicroViaTop2,
        ExampleSubstrate.MicroViaTop3,
        ExampleSubstrate.MicroViaTop4,
        ExampleSubstrate.DefaultTHVia,
    ]
