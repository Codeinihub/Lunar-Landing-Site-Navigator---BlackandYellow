import numpy as np
import pandas as pd

from data.preprocessing import (
    preprocess_data,
    get_data_quality,
    aggregate_annual
)


# Daily test
daily_data = [
    {"date": "20230103", "value": -10.2},
    {"date": "20230101", "value": -12.5},
    {"date": "20230102", "value": -999},
]

# Monthly test
monthly_data = [
    {"date": "202301", "value": -12.5},
    {"date": "202302", "value": -10.2},
]

# Hourly test
hourly_data = [
    {"date": "2023010102", "value": -9.49},
    {"date": "2023010100", "value": -9.41},
    {"date": "2023010101", "value": -999},
]


test_cases = {
    "DAILY": daily_data,
    "MONTHLY": monthly_data,
    "HOURLY": hourly_data
}


for name, sample in test_cases.items():

    print(f"\n{'=' * 35}")
    print(f"TESTING {name} DATA")
    print("=" * 35)

    df = preprocess_data(sample)

    print(df)

    print("\nData quality:")
    print(get_data_quality(df))

    # Confirm chronological ordering
    assert df["date"].is_monotonic_increasing

    # Confirm NASA missing values were handled
    assert not (df["value"] == -999).any()

    print("\nAll tests passed!")

def test_annual_aggregation():
    print("\n===================================")
    print("TESTING ANNUAL AGGREGATION")
    print("===================================")

    # Test 1: Complete daily data for 2023.
    daily_dates = pd.date_range(
        start="2023-01-01",
        end="2023-12-31",
        freq="D"
    )

    daily_data = pd.DataFrame({
        "date": daily_dates,
        "value": np.full(len(daily_dates), 10.0)
    })

    result = aggregate_annual(
        daily_data,
        temporal_resolution="daily"
    )

    print("\nComplete daily dataset:")
    print(result)

    assert len(result) == 1
    assert result.iloc[0]["year"] == 2023
    assert result.iloc[0]["expected_observations"] == 365
    assert result.iloc[0]["valid_observations"] == 365
    assert result.iloc[0]["annual_average"] == 10.0
    assert result.iloc[0]["eligible_for_trend"] == True

    # Test 2: Missing measurements should reduce completeness.
    incomplete_data = daily_data.copy()
    incomplete_data.loc[0:49, "value"] = np.nan

    result = aggregate_annual(
        incomplete_data,
        temporal_resolution="daily"
    )

    print("\nIncomplete daily dataset:")
    print(result)

    assert result.iloc[0]["valid_observations"] == 315
    assert result.iloc[0]["completeness_percentage"] < 90
    assert result.iloc[0]["annual_average"] == 10.0
    # assert result.iloc[0]["annual_average"] == 10.0
    # assert pd.isna(result.iloc[0]["annual_average"])
    assert result.iloc[0]["eligible_for_trend"] == False

    # Test 3: Leap year should have 366 expected daily observations.
    leap_dates = pd.date_range(
        start="2024-01-01",
        end="2024-12-31",
        freq="D"
    )

    leap_data = pd.DataFrame({
        "date": leap_dates,
        "value": np.full(len(leap_dates), 15.0)
    })

    result = aggregate_annual(
        leap_data,
        temporal_resolution="daily"
    )

    assert result.iloc[0]["expected_observations"] == 366
    assert result.iloc[0]["annual_average"] == 15.0

    # Test 4: Monthly data should expect 12 observations.
    monthly_dates = pd.date_range(
        start="2023-01-01",
        end="2023-12-01",
        freq="MS"
    )

    monthly_data = pd.DataFrame({
        "date": monthly_dates,
        "value": np.full(12, 20.0)
    })

    result = aggregate_annual(
        monthly_data,
        temporal_resolution="monthly"
    )

    assert result.iloc[0]["expected_observations"] == 12
    assert result.iloc[0]["annual_average"] == 20.0

    # Test 5: Hourly data should expect 8,760 observations in 2023.
    hourly_dates = pd.date_range(
        start="2023-01-01",
        end="2024-01-01",
        freq="h",
        inclusive="left"
    )

    hourly_data = pd.DataFrame({
        "date": hourly_dates,
        "value": np.full(len(hourly_dates), 5.0)
    })

    result = aggregate_annual(
        hourly_data,
        temporal_resolution="hourly"
    )

    assert result.iloc[0]["expected_observations"] == 8760
    assert result.iloc[0]["annual_average"] == 5.0

    print("\nAll annual aggregation tests passed!")


if __name__ == "__main__":
    test_annual_aggregation()
