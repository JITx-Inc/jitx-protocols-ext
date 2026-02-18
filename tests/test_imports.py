"""Test that all public exports import correctly."""

import importlib


def test_top_level_import():
    """Package root imports without error."""
    mod = importlib.import_module("jitx_protocols_ext")
    assert hasattr(mod, "__all__")


def test_all_exports_accessible():
    """Every name in __all__ is importable from the top-level package."""
    import jitx_protocols_ext

    for name in jitx_protocols_ext.__all__:
        obj = getattr(jitx_protocols_ext, name)
        assert obj is not None, f"{name} resolved to None"


def test_protocols_subpackage():
    """Protocols subpackage imports."""
    from jitx_protocols_ext.protocols import (
        JESD204,
        SATA,
        PCIe,
        SFP_Lane,
    )

    assert JESD204 is not None
    assert PCIe is not None
    assert SATA is not None
    assert SFP_Lane is not None


def test_memory_subpackage():
    """Memory protocols subpackage imports."""
    from jitx_protocols_ext.protocols.memory import (
        DDR4,
        GDDR7,
        LPDDR4,
        LPDDR5,
    )

    assert DDR4 is not None
    assert GDDR7 is not None
    assert LPDDR4 is not None
    assert LPDDR5 is not None


def test_common_subpackage():
    """Common infrastructure subpackage imports."""
    from jitx_protocols_ext.common.example_board import ExampleBoard, ExampleSubstrate
    from jitx_protocols_ext.common.example_components import BlockingCapacitor

    assert ExampleBoard is not None
    assert ExampleSubstrate is not None
    assert BlockingCapacitor is not None


def test_examples_subpackage():
    """Example subpackages import without error."""
    from jitx_protocols_ext.examples.protocols.jesd204 import (
        JESD204ADCComponent,
        JESD204ExampleDesign,
    )
    from jitx_protocols_ext.examples.protocols.pcie import PCIeSwitchComponent  # noqa: F401
    from jitx_protocols_ext.examples.protocols.sata import SATASwitchComponent

    assert JESD204ADCComponent is not None
    assert JESD204ExampleDesign is not None
    assert SATASwitchComponent is not None
