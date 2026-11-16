
import pytest

from backend.main import (
    prepare_measurements,
    aggregate_annual
)


def test_monthly_date_conversion():

    measurements = [
        {"date": "201001", "value": 2.5},
        {"date": "201002", "value": 3.5},
        {"date": "201013", "value": 3.0}
    ]

    df = prepare_measurements(
        measurements,
        "monthly"
    )

    assert len(df) == 2
    assert df.iloc[0]["date"].year == 2010
    assert df.iloc[0]["date"].month == 1


def test_missing_measurements():

    measurements = [
        {"date": "201001", "value": 2.5},
        {"date": "201002", "value": -999},
        {"date": "201003", "value": 4.5}
    ]

    df = prepare_measurements(
        measurements,
        "monthly"
    )

    assert len(df) == 3
    assert df["value"].isna().sum() == 1


def test_incomplete_year():

    measurements = [
        {
            "date": f"2026{month:02d}",
            "value": 5.0
        }
        for month in range(1, 10)
    ]

    df = prepare_measurements(
        measurements,
        "monthly"
    )

    annual = aggregate_annual(
        df,
        temporal_resolution="monthly",
        min_completeness=90
    )

    assert annual.iloc[0]["valid_observations"] == 9
    assert annual.iloc[0]["completeness_percent"] == 75
    assert not bool(annual.iloc[0]["eligible_for_trend"])
