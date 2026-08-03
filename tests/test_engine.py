import pytest

from core.engine import CRCEngine


def test_calculate_appends_zeros_and_returns_remainder_row():
    _, rows, dividend = CRCEngine.calculate("110101", "1011")
    assert dividend == "110101000"  # data + (n-1) zeros
    assert rows and rows[-1]["type"] == "remainder"
    crc = rows[-1]["val"][-(len("1011") - 1) :]
    assert crc == "111"


def test_verify_valid_frame():
    _, _, _, remainder, is_valid = CRCEngine.verify("110101111", "1011")
    assert is_valid is True
    assert remainder == "000"


def test_verify_invalid_frame():
    _, _, _, remainder, is_valid = CRCEngine.verify("110101110", "1011")
    assert is_valid is False
    assert remainder != "000"


@pytest.mark.parametrize(
    ("data", "divisor"),
    [("110101", "1011"), ("1011001", "100000111"), ("1", "1011")],
)
def test_calculate_then_verify_roundtrip(data, divisor):
    _, rows, _ = CRCEngine.calculate(data, divisor)
    crc = rows[-1]["val"][-(len(divisor) - 1) :]
    _, _, _, remainder, is_valid = CRCEngine.verify(data + crc, divisor)
    assert is_valid is True
    assert remainder == "0" * (len(divisor) - 1)


def test_remainder_width_matches_polynomial_order():
    divisor = "100000111"
    _, rows, _ = CRCEngine.calculate("1011001", divisor)
    crc = rows[-1]["val"][-(len(divisor) - 1) :]
    assert len(crc) == len(divisor) - 1


def test_empty_data_returns_empty():
    q, rows, dividend = CRCEngine.calculate("", "1011")
    assert q == "" and rows == [] and dividend == ""


def test_divisor_starting_with_zero_rejected():
    q, rows, dividend = CRCEngine.calculate("110101", "0111")
    assert q == "" and rows == [] and dividend == ""


def test_verify_frame_shorter_than_divisor():
    _, rows, _, _, is_valid = CRCEngine.verify("101", "1011")
    assert is_valid is False
    assert rows == []
