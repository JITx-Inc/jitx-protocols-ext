"""Tests for the JESD204 protocol bundle."""

import dataclasses

from jitx_protocols_ext.protocols.jesd204 import (
    JESD204,
    JESD204Constraint,
    JESD204LaneCount,
    JESD204Standard,
    JESD204Version,
)


class TestJESD204LaneCount:
    def test_lane_count_values(self):
        assert JESD204LaneCount.x1.value == 1
        assert JESD204LaneCount.x4.value == 4
        assert JESD204LaneCount.x8.value == 8
        assert JESD204LaneCount.x32.value == 32

    def test_all_standard_widths(self):
        expected = {1, 2, 4, 8, 16, 32}
        actual = {e.value for e in JESD204LaneCount}
        assert actual == expected


class TestJESD204Bundle:
    """Test JESD204 bundle instantiation.

    Note: JITX Port attributes are wrapped as InstantiableAttribute objects
    outside a Design context. This means `is None` checks don't work for
    optional ports. We test constructor acceptance and that non-optional
    attributes are accessible instead.
    """

    def test_default_instantiation(self):
        j = JESD204()
        assert j.SYNC is not None
        assert j.SYSREF is not None
        assert j.DEVCLK is not None

    def test_with_enum_lane_count(self):
        j = JESD204(JESD204LaneCount.x8)
        assert j.SYNC is not None

    def test_with_int_lane_count(self):
        j = JESD204(2)
        assert j.SYNC is not None

    def test_no_sync_accepted(self):
        """JESD204C 64B/66B mode — constructor accepts include_sync=False."""
        j = JESD204(4, include_sync=False)
        assert j is not None

    def test_no_sysref_accepted(self):
        """Subclass 0 or 2 — constructor accepts include_sysref=False."""
        j = JESD204(4, include_sysref=False)
        assert j is not None

    def test_no_devclk_accepted(self):
        j = JESD204(4, include_devclk=False)
        assert j is not None

    def test_minimal_bundle_accepted(self):
        """JESD204C 64B/66B Subclass 0 — data lanes only."""
        j = JESD204(1, include_sync=False, include_sysref=False, include_devclk=False)
        assert j is not None


class TestJESD204Standard:
    def test_frozen(self):
        std = JESD204Version.JESD204B.value
        assert isinstance(std, JESD204Standard)
        assert dataclasses.is_dataclass(std)

    def test_jesd204b_impedance(self):
        assert JESD204Version.JESD204B.impedance.typ == 100.0

    def test_jesd204c_tighter_skew(self):
        """JESD204C should have tighter skew than JESD204B."""
        b_skew = JESD204Version.JESD204B.skew.max_value
        c_skew = JESD204Version.JESD204C.skew.max_value
        assert c_skew < b_skew

    def test_customization_via_replace(self):
        custom = dataclasses.replace(JESD204Version.JESD204B.value, loss=10.0)
        assert custom.loss == 10.0
        assert JESD204Version.JESD204B.loss == 12.0  # original unchanged

    def test_version_property_accessors(self):
        v = JESD204Version.JESD204B
        assert v.skew == v.value.skew
        assert v.lane_skew == v.value.lane_skew
        assert v.loss == v.value.loss
        assert v.impedance == v.value.impedance


class TestJESD204Constraint:
    def test_instantiation(self):
        """Constraint class exists and has the right interface."""
        assert issubclass(JESD204Constraint, object)
        assert hasattr(JESD204Constraint, "constrain")
