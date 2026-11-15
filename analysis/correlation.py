
import numpy as np
import pandas as pd
from scipy.stats import norm


def calculate_mann_kendall(annual_data, alpha=0.05):
    """
    Perform the Mann-Kendall test for a monotonic trend.

    Parameters
    ----------
    annual_data : pandas.DataFrame
        Must contain 'year' and 'annual_average'.
        Optionally contains 'eligible_for_trend'.

    alpha : float
        Significance level. Defaults to 0.05.

    Returns
    -------
    dict
        Mann-Kendall test statistics and trend interpretation.
    """

    # 1. Validate inputs
    required_columns = {"year", "annual_average"}

    if not isinstance(annual_data, pd.DataFrame):
        raise ValueError("annual_data must be a pandas DataFrame.")

    if not required_columns.issubset(annual_data.columns):
        raise ValueError("Data must contain year and annual_average.")

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    df = annual_data.copy()

    # 2. Exclude years that failed data-quality requirements
    if "eligible_for_trend" in df.columns:
        df = df[df["eligible_for_trend"] == True]

    # 3. Clean and validate values
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["annual_average"] = pd.to_numeric(
        df["annual_average"], errors="coerce"
    )

    df = df.dropna(subset=["year", "annual_average"])

    df = df[
        np.isfinite(df["year"]) &
        np.isfinite(df["annual_average"])
    ]

    df = df.sort_values("year")

    if df["year"].duplicated().any():
        raise ValueError("Duplicate years are not allowed.")

    if len(df) < 3:
        raise ValueError(
            "At least 3 eligible annual observations are required."
        )

    years = df["year"].to_numpy()
    values = df["annual_average"].to_numpy()

    # 4. Calculate the S statistic
    s = 0

    for i in range(len(values) - 1):
        for j in range(i + 1, len(values)):
            difference = values[j] - values[i]

            if difference > 0:
                s += 1
            elif difference < 0:
                s -= 1

    # 5. Calculate variance, correcting for tied values
    n = len(values)

    _, tie_counts = np.unique(values, return_counts=True)

    tie_correction = sum(
        count * (count - 1) * (2 * count + 5)
        for count in tie_counts
    )

    variance_s = (
        n * (n - 1) * (2 * n + 5) - tie_correction
    ) / 18

    # 6. Calculate standardized Z statistic
    if variance_s == 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / np.sqrt(variance_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(variance_s)
    else:
        z = 0.0

    # 7. Calculate two-sided p-value
    p_value = 2 * norm.sf(abs(z))

    # 8. Interpret the result
    # is_significant = p_value < alpha

    # if not is_significant:
    #     trend_direction = "no_significant_trend"
    # elif s > 0:
    #     trend_direction = "increasing"
    # elif s < 0:
    #     trend_direction = "decreasing"
    # else:
    #     trend_direction = "no_significant_trend"
        # 8. Interpret direction and statistical significance

    if s > 0:
        observed_direction = "increasing"
    elif s < 0:
        observed_direction = "decreasing"
    else:
        observed_direction = "stable"

    is_significant = p_value < alpha

    if is_significant:
        trend_direction = observed_direction
    else:
        trend_direction = "no_significant_trend"

    return {
        "method": "mann_kendall",
        "observed_direction": observed_direction,
        "trend_direction": trend_direction,
        "s_statistic": int(s),
        "variance_s": float(variance_s),
        "z_statistic": float(z),
        "p_value": float(p_value),
        "alpha": alpha,
        "is_significant": bool(is_significant),
        "years_analyzed": years.tolist(),
        "observed_values": values.tolist()
    }
