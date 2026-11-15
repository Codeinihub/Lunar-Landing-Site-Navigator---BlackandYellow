import numpy as np
import pandas as pd

from analysis.trends import (
    calculate_linear_regression,
    calculate_sens_slope
)

from analysis.correlation import calculate_mann_kendall


def analyze_annual_trends(annual_data, alpha=0.05):
    """
    Run all three trend-analysis methods on annual environmental data.

    Parameters
    ----------
    annual_data : pandas.DataFrame
        Output from aggregate_annual().
        Required columns:
            - year
            - annual_average
        Optional:
            - eligible_for_trend

    alpha : float
        Significance threshold for the Mann-Kendall test.

    Returns
    -------
    dict
        Combined results from linear regression,
        Sen's slope, and Mann-Kendall.
    """

    # 1. Validate input
    if not isinstance(annual_data, pd.DataFrame):
        raise ValueError("annual_data must be a pandas DataFrame.")

    if annual_data.empty:
        raise ValueError("No annual data was provided.")

    required_columns = {"year", "annual_average"}

    if not required_columns.issubset(annual_data.columns):
        raise ValueError(
            "Data must contain year and annual_average columns."
        )

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    # 2. Identify eligible observations
    eligible_data = annual_data.copy()

    if "eligible_for_trend" in eligible_data.columns:
        eligible_data = eligible_data[
            eligible_data["eligible_for_trend"] == True
        ]

    eligible_data["year"] = pd.to_numeric(
        eligible_data["year"], errors="coerce"
    )

    eligible_data["annual_average"] = pd.to_numeric(
        eligible_data["annual_average"], errors="coerce"
    )

    # eligible_data = eligible_data.dropna(
    #     subset=["year", "annual_average"]
    # )

    # eligible_data = eligible_data[
    #     eligible_data["year"].map(pd.notna) &
    #     eligible_data["annual_average"].map(pd.notna)
    # ]
    eligible_data = eligible_data.dropna(
        subset=["year", "annual_average"]
    )

    eligible_data = eligible_data[
        np.isfinite(eligible_data["year"]) &
        np.isfinite(eligible_data["annual_average"])
    ]

    if eligible_data["year"].duplicated().any():
        raise ValueError("Duplicate years found in annual data.")

    # All three methods require at least 3 observations
    # because Mann-Kendall requires at least 3.
    if len(eligible_data) < 3:
        raise ValueError(
            "At least 3 eligible annual observations "
            "are required for the complete trend analysis."
        )

    # 3. Run the three analysis methods
    linear_results = calculate_linear_regression(annual_data)

    sen_results = calculate_sens_slope(annual_data)

    mann_kendall_results = calculate_mann_kendall(
        annual_data,
        alpha=alpha
    )

    # 4. Combine results
    return {
        "years_analyzed": linear_results["years_analyzed"],

        "summary": {
            "linear_regression_direction":
                linear_results["trend_direction"],

            "sens_slope_direction":
                sen_results["trend_direction"],

            "observed_direction":
                mann_kendall_results["observed_direction"],

            "is_significant":
                mann_kendall_results["is_significant"],

            "p_value":
                mann_kendall_results["p_value"]
        },

        "methods": {
            "linear_regression": linear_results,
            "sens_slope": sen_results,
            "mann_kendall": mann_kendall_results
        }
    }
