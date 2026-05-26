import pytest
from datetime import datetime, timezone
from pathlib import Path

from custom_components.creg.coordinator import _parse_csv, CregCoordinator, RegionData, MonthData

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


def _make_now(year: int, month: int) -> datetime:
    return datetime(year, month, 15, tzinfo=timezone.utc)


def test_this_quarter_avg_returns_q2_value_for_may():
    # Q2/2026 (Apr-Jun): rate is published in the January 2026 row
    rows = _load_fixture()

    class _Stub:
        data = rows

    result = CregCoordinator.this_quarter_avg(_Stub(), "flanders", now=_make_now(2026, 5))
    assert result is not None
    assert result.value == pytest.approx(31.91)
    assert result.year == 2026
    assert result.month == 4  # Q2 start


def test_this_quarter_avg_returns_q2_value_for_april():
    rows = _load_fixture()

    class _Stub:
        data = rows

    result = CregCoordinator.this_quarter_avg(_Stub(), "flanders", now=_make_now(2026, 4))
    assert result is not None
    assert result.value == pytest.approx(31.91)
    assert result.year == 2026
    assert result.month == 4


def test_this_quarter_avg_returns_q2_value_for_june():
    rows = _load_fixture()

    class _Stub:
        data = rows

    result = CregCoordinator.this_quarter_avg(_Stub(), "flanders", now=_make_now(2026, 6))
    assert result is not None
    assert result.value == pytest.approx(31.91)
    assert result.year == 2026
    assert result.month == 4


def test_this_quarter_avg_returns_q3_value_for_july():
    # Q3/2026 (Jul-Sep): rate is published in the April 2026 row
    rows = _load_fixture()

    class _Stub:
        data = rows

    result = CregCoordinator.this_quarter_avg(_Stub(), "flanders", now=_make_now(2026, 7))
    assert result is not None
    assert result.value == pytest.approx(32.22)
    assert result.year == 2026
    assert result.month == 7  # Q3 start


def test_this_quarter_avg_returns_none_for_unpublished_quarter():
    rows = _load_fixture()

    class _Stub:
        data = rows

    # Q4/2026 (Oct-Dec): rate would be in the July 2026 row, which is not in the fixture
    result = CregCoordinator.this_quarter_avg(_Stub(), "flanders", now=_make_now(2026, 10))
    assert result is None


def test_this_quarter_avg_returns_none_when_avg_3m_is_null():
    # Q2 (May) looks for the January row; avg_3m=None on that row → None
    rows = [
        MonthData(year=2026, month=1, flanders=RegionData(price=31.0, avg_3m=None),
                  brussels=RegionData(price=36.0, avg_3m=None),
                  wallonia=RegionData(price=37.0, avg_3m=None)),
    ]

    class _Stub:
        data = rows

    result = CregCoordinator.this_quarter_avg(_Stub(), "flanders", now=_make_now(2026, 5))
    assert result is None


def test_this_quarter_avg_no_data():
    class _Stub:
        data = []

    assert CregCoordinator.this_quarter_avg(_Stub(), "flanders", now=_make_now(2026, 5)) is None


@pytest.mark.parametrize("month,expected_q_start", [
    (1, 1), (2, 1), (3, 1),
    (4, 4), (5, 4), (6, 4),
    (7, 7), (8, 7), (9, 7),
    (10, 10), (11, 10), (12, 10),
])
def test_this_quarter_avg_quarter_boundaries(month, expected_q_start):
    # Include Oct 2025 so Q1/2026 (Jan-Mar) can find its published row
    rows = [
        MonthData(year=2025, month=10, flanders=RegionData(price=30.0, avg_3m=31.0),
                  brussels=RegionData(price=35.0, avg_3m=None),
                  wallonia=RegionData(price=36.0, avg_3m=None)),
    ] + [
        MonthData(year=2026, month=m, flanders=RegionData(price=30.0, avg_3m=31.0 if m in {1, 4, 7} else None),
                  brussels=RegionData(price=35.0, avg_3m=None),
                  wallonia=RegionData(price=36.0, avg_3m=None))
        for m in range(1, 13)
    ]

    class _Stub:
        data = rows

    result = CregCoordinator.this_quarter_avg(_Stub(), "flanders", now=_make_now(2026, month))
    assert result is not None
    assert result.month == expected_q_start
