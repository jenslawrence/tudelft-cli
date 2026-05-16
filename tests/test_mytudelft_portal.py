from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal


def test_format_time_decimal_formats_numeric_values() -> None:
    assert MyTUDelftPortal._format_time_decimal("9.5") == "09:30"


def test_format_time_decimal_keeps_non_numeric_values() -> None:
    assert MyTUDelftPortal._format_time_decimal("morning") == "morning"
