"""Tests for the DDR5 protocol bundle.

Note: JITX Port attributes are wrapped as InstantiableAttribute objects
outside a Design context. This means `len()` and `is None` checks don't work
for Port-based attributes. We test constructor acceptance and that
non-optional attributes are accessible instead.
"""

from jitx_protocols_ext.protocols.memory.ddr5 import (
    DDR5,
    DDR5CAChannel,
    DDR5Constraint,
    DDR5DataChannel,
    DDR5Impedances,
    DDR5Rank,
    DDR5Width,
    rank_to_int,
    width_to_int,
    width_to_lane_count,
)


class TestDDR5Width:
    def test_width_values(self):
        assert DDR5Width.x8.value == 8
        assert DDR5Width.x16.value == 16
        assert DDR5Width.x32.value == 32
        assert DDR5Width.x40.value == 40
        assert DDR5Width.x64.value == 64
        assert DDR5Width.x72.value == 72

    def test_all_widths(self):
        expected = {8, 16, 32, 40, 64, 72}
        actual = {e.value for e in DDR5Width}
        assert actual == expected

    def test_width_to_int(self):
        assert width_to_int(DDR5Width.x16) == 16
        assert width_to_int(DDR5Width.x64) == 64

    def test_width_to_lane_count(self):
        assert width_to_lane_count(DDR5Width.x8) == 1
        assert width_to_lane_count(DDR5Width.x16) == 2
        assert width_to_lane_count(DDR5Width.x32) == 4
        assert width_to_lane_count(DDR5Width.x40) == 5
        assert width_to_lane_count(DDR5Width.x64) == 8
        assert width_to_lane_count(DDR5Width.x72) == 9


class TestDDR5Rank:
    def test_rank_values(self):
        assert DDR5Rank.SingleRank.value == 1
        assert DDR5Rank.DualRank.value == 2
        assert DDR5Rank.QuadRank.value == 4

    def test_rank_to_int(self):
        assert rank_to_int(DDR5Rank.SingleRank) == 1
        assert rank_to_int(DDR5Rank.DualRank) == 2


class TestDDR5DataChannel:
    def test_x8_accepted(self):
        ch = DDR5DataChannel(DDR5Width.x8)
        assert ch is not None

    def test_x16_accepted(self):
        ch = DDR5DataChannel(DDR5Width.x16)
        assert ch is not None

    def test_x32_accepted(self):
        ch = DDR5DataChannel(DDR5Width.x32)
        assert ch is not None

    def test_x72_accepted(self):
        ch = DDR5DataChannel(DDR5Width.x72)
        assert ch is not None

    def test_has_expected_attributes(self):
        ch = DDR5DataChannel(DDR5Width.x16)
        assert hasattr(ch, "DQ")
        assert hasattr(ch, "DQS")
        assert hasattr(ch, "DMI")


class TestDDR5CAChannel:
    def test_single_rank_accepted(self):
        ch = DDR5CAChannel(DDR5Rank.SingleRank)
        assert ch is not None

    def test_dual_rank_accepted(self):
        ch = DDR5CAChannel(DDR5Rank.DualRank)
        assert ch is not None

    def test_quad_rank_accepted(self):
        ch = DDR5CAChannel(DDR5Rank.QuadRank)
        assert ch is not None

    def test_has_expected_attributes(self):
        ch = DDR5CAChannel(DDR5Rank.SingleRank)
        assert hasattr(ch, "CK")
        assert hasattr(ch, "CA")
        assert hasattr(ch, "CS_n")
        assert hasattr(ch, "CKE")
        assert hasattr(ch, "ODT")
        assert hasattr(ch, "RESET_n")
        assert hasattr(ch, "ALERT_n")


class TestDDR5Bundle:
    def test_default_instantiation(self):
        d = DDR5(DDR5Width.x16)
        assert d.data is not None
        assert d.ca is not None

    def test_x16_single_rank_accepted(self):
        d = DDR5(DDR5Width.x16, DDR5Rank.SingleRank)
        assert d is not None

    def test_x32_dual_rank_accepted(self):
        d = DDR5(DDR5Width.x32, DDR5Rank.DualRank)
        assert d is not None

    def test_x64_single_rank_accepted(self):
        d = DDR5(DDR5Width.x64)
        assert d is not None

    def test_x72_ecc_accepted(self):
        d = DDR5(DDR5Width.x72)
        assert d is not None

    def test_all_widths_instantiate(self):
        for width in DDR5Width:
            d = DDR5(width)
            assert d is not None

    def test_all_ranks_instantiate(self):
        for rank in DDR5Rank:
            d = DDR5(DDR5Width.x16, rank)
            assert d is not None


class TestDDR5Impedances:
    def test_default_impedances(self):
        imp = DDR5Impedances()
        assert imp.ck_impedance.typ == 80.0
        assert imp.dqs_impedance.typ == 80.0
        assert imp.dq_impedance.typ == 40.0
        assert imp.ca_impedance.typ == 40.0

    def test_impedances_are_tighter_than_ddr4(self):
        """DDR5 uses lower impedances than DDR4."""
        from jitx_protocols_ext.protocols.memory.ddr4 import DDR4Impedances

        ddr4 = DDR4Impedances()
        ddr5 = DDR5Impedances()
        assert ddr5.ck_impedance.typ < ddr4.ck_impedance.typ
        assert ddr5.dqs_impedance.typ < ddr4.dqs_impedance.typ
        assert ddr5.dq_impedance.typ < ddr4.dq_impedance.typ
        assert ddr5.ca_impedance.typ < ddr4.acc_impedance.typ


class TestDDR5Constraint:
    def test_has_constrain_method(self):
        assert hasattr(DDR5Constraint, "constrain")
