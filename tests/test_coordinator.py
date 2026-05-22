import pytest
from pathlib import Path

from custom_components.creg.coordinator import _parse_csv, CregCoordinator

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "creg_tariff_ev.csv"


def _load_fixture() -> list:
    text = FIXTURE_PATH.read_text(encoding="utf-8-sig")
    return _parse_csv(text)


def test_parse_csv_row_count():
    rows = _load_fixture()
    assert len(rows) == 10


def test_parse_csv_sorted_descending():
    rows = _load_fixture()
    years_months = [(r.year, r.month) for r in rows]
    assert years_months == sorted(years_months, reverse=True)


def test_parse_csv_latest_row():
    rows = _load_fixture()
    latest = rows[0]
    assert latest.year == 2026
    assert latest.month == 4
    assert latest.flanders.price == pytest.approx(32.71)
    assert latest.flanders.avg_3m == pytest.approx(32.22)
    assert latest.brussels.price == pytest.approx(37.64)
    assert latest.brussels.avg_3m == pytest.approx(37.19)
    assert latest.wallonia.price == pytest.approx(38.38)
    assert latest.wallonia.avg_3m == pytest.approx(37.83)


def test_parse_csv_missing_avg_3m():
    rows = _load_fixture()
    march_2026 = next(r for r in rows if r.year == 2026 and r.month == 3)
    assert march_2026.flanders.avg_3m is None
    assert march_2026.brussels.avg_3m is None
    assert march_2026.wallonia.avg_3m is None


def test_parse_csv_integer_price():
    rows = _load_fixture()
    jan_2026 = next(r for r in rows if r.year == 2026 and r.month == 1)
    assert jan_2026.brussels.price == pytest.approx(36.0)


def test_latest_avg_3m_returns_most_recent_quarterly():
    rows = _load_fixture()

    class _Stub:
        data = rows

    result = CregCoordinator.latest_avg_3m(_Stub(), "flanders")
    assert result is not None
    assert result.value == pytest.approx(32.22)
    assert result.year == 2026
    assert result.month == 4


def test_latest_avg_3m_all_regions():
    rows = _load_fixture()

    class _Stub:
        data = rows

    for region, expected in [
        ("flanders", 32.22),
        ("brussels", 37.19),
        ("wallonia", 37.83),
    ]:
        result = CregCoordinator.latest_avg_3m(_Stub(), region)
        assert result is not None
        assert result.value == pytest.approx(expected)
        assert result.year == 2026
        assert result.month == 4


def test_latest_price_no_data():
    class _Stub:
        data = []

    assert CregCoordinator.latest_price(_Stub(), "flanders") is None


def test_latest_avg_3m_no_data():
    class _Stub:
        data = []

    assert CregCoordinator.latest_avg_3m(_Stub(), "flanders") is None
