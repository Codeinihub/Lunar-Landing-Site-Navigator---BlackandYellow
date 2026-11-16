
# import pandas as pd
# import numpy as np


# def preprocess_data(data):
#     """Convert raw NASA measurements into a clean DataFrame."""

#     # Check that data was returned
#     if not data:
#         raise ValueError("No data was provided.")

#     df = pd.DataFrame(data)

#     # Check that the expected columns exist
#     required_columns = {"date", "value"}

#     if not required_columns.issubset(df.columns):
#         raise ValueError("Data must contain date and value columns.")

#     # Convert dates and measurements to appropriate types
#     # df["date"] = pd.to_datetime(
#     #     df["date"],
#     #     format="%Y%m%d",
#     #     errors="coerce"
#     # )
#     df["date"] = pd.to_datetime(
#         df["date"],
#         errors="coerce"
#     )

#     df["value"] = pd.to_numeric(
#         df["value"],
#         errors="coerce"
#     )

#     # Replace NASA's missing-value marker
#     df["value"] = df["value"].replace(-999, np.nan)

#     # Sort chronologically
#     df = df.sort_values("date")

#     # Remove rows with invalid dates, but preserve missing measurements
#     df = df.dropna(subset=["date"])

#     # Reset index
#     df = df.reset_index(drop=True)

#     return df


# def get_data_quality(df):
#     """Calculate basic data completeness statistics."""

#     total = len(df)
#     valid = df["value"].count()
#     missing = df["value"].isna().sum()

#     completeness = (
#         (valid / total) * 100
#         if total > 0 else 0
#     )

#     return {
#         "total_observations": int(total),
#         "valid_observations": int(valid),
#         "missing_observations": int(missing),
#         "completeness_percentage": round(completeness, 2)
#     }

import pandas as pd
import numpy as np


def preprocess_data(data):
    """Convert raw NASA measurements into a clean DataFrame."""

    # 1. Check that data was returned
    if data is None or len(data) == 0:
        raise ValueError("No data was provided.")

    df = pd.DataFrame(data)

    # 2. Check required columns
    required_columns = {"date", "value"}

    if not required_columns.issubset(df.columns):
        raise ValueError(
            "Data must contain date and value columns."
        )

    # 3. Normalize date strings
    raw_dates = df["date"].astype("string").str.strip()

    parsed_dates = pd.Series(
        pd.NaT,
        index=df.index,
        dtype="datetime64[ns]"
    )

    # NASA monthly format: YYYYMM
    monthly = raw_dates.str.fullmatch(r"\d{6}").fillna(False)

    parsed_dates.loc[monthly] = pd.to_datetime(
        raw_dates.loc[monthly],
        format="%Y%m",
        errors="coerce"
    )

    # NASA daily format: YYYYMMDD
    daily = raw_dates.str.fullmatch(r"\d{8}").fillna(False)

    parsed_dates.loc[daily] = pd.to_datetime(
        raw_dates.loc[daily],
        format="%Y%m%d",
        errors="coerce"
    )

    # NASA hourly format: YYYYMMDDHH
    hourly = raw_dates.str.fullmatch(r"\d{10}").fillna(False)

    parsed_dates.loc[hourly] = pd.to_datetime(
        raw_dates.loc[hourly],
        format="%Y%m%d%H",
        errors="coerce"
    )

    # Other formats, such as ISO timestamps
    other = ~(monthly | daily | hourly)

    parsed_dates.loc[other] = pd.to_datetime(
        raw_dates.loc[other],
        errors="coerce"
    )

    df["date"] = parsed_dates

    # 4. Convert measurements to numeric
    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce"
    )

    # 5. Replace NASA missing-value marker
    df["value"] = df["value"].replace(-999, np.nan)

    # 6. Remove invalid dates
    df = df.dropna(subset=["date"])

    # 7. Sort chronologically
    df = df.sort_values("date")

    # 8. Reset index
    df = df.reset_index(drop=True)

    return df


def get_data_quality(df):
    """Calculate basic data completeness statistics."""

    if not {"date", "value"}.issubset(df.columns):
        raise ValueError(
            "DataFrame must contain date and value columns."
        )

    total = len(df)
    valid = int(df["value"].count())
    missing = int(df["value"].isna().sum())

    completeness = (
        (valid / total) * 100
        if total > 0 else 0
    )

    return {
        "total_observations": int(total),
        "valid_observations": valid,
        "missing_observations": missing,
        "completeness_percentage": round(
            completeness, 2
        )
    }

def aggregate_annual(df, temporal_resolution="daily", min_completeness=90.0):
    """
    Aggregate measurements into annual averages.

    Parameters:
        df: Cleaned DataFrame containing 'date' and 'value' columns.
        temporal_resolution: 'hourly', 'daily', or 'monthly'.
        min_completeness: Minimum percentage of expected observations
                          required for a year to qualify for trend analysis.

    Returns:
        DataFrame with one row per calendar year.
    """

    required_columns = {"date", "value"}

    if not required_columns.issubset(df.columns):
        raise ValueError("DataFrame must contain date and value columns.")

    if df.empty:
        raise ValueError("Cannot aggregate an empty DataFrame.")

    if temporal_resolution not in {"hourly", "daily", "monthly"}:
        raise ValueError(
            "temporal_resolution must be hourly, daily, or monthly."
        )

    if not 0 <= min_completeness <= 100:
        raise ValueError("min_completeness must be between 0 and 100.")

    data = df.copy()

    # Ensure dates and values have the correct types.
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")

    # Invalid dates cannot be grouped into calendar years.
    data = data.dropna(subset=["date"])

    if data.empty:
        raise ValueError("No valid dates were available for aggregation.")

    # Duplicate timestamps could artificially inflate observation counts.
    if data["date"].duplicated().any():
        raise ValueError("Duplicate dates found in the dataset.")

    data["year"] = data["date"].dt.year

    annual_results = []

    for year, group in data.groupby("year"):

        # Account for leap years.
        days_in_year = (
            366 if pd.Timestamp(year=year, month=12, day=31).dayofyear == 366
            else 365
        )

        # Calculate the number of observations expected in a full year.
        if temporal_resolution == "hourly":
            expected = days_in_year * 24
        elif temporal_resolution == "daily":
            expected = days_in_year
        else:
            expected = 12

        valid = int(group["value"].count())

        completeness = (valid / expected) * 100

        # Calculate the average only if the year meets the threshold.
        # average = (
        #     group["value"].mean()
        #     if completeness >= min_completeness
        #     else np.nan
        # )
        average = group["value"].mean()
        
        annual_results.append({
            "year": int(year),
            "annual_average": average,
            "valid_observations": valid,
            "expected_observations": expected,
            "completeness_percentage": round(completeness, 2),
            "eligible_for_trend": completeness >= min_completeness
        })

    return pd.DataFrame(annual_results)
