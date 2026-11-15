
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def calculate_linear_regression(annual_data):
    """
    Calculate a linear trend from annual environmental measurements.

    Parameters:
        annual_data: DataFrame produced by aggregate_annual().
                     Required columns:
                     - year
                     - annual_average
                     - eligible_for_trend (optional)

    Returns:
        Dictionary containing the trend slope, intercept,
        R-squared, and fitted values.
    """

    required_columns = {"year", "annual_average"}

    if not required_columns.issubset(annual_data.columns):
        raise ValueError(
            "Data must contain year and annual_average columns."
        )

    if annual_data.empty:
        raise ValueError("No annual data was provided.")

    data = annual_data.copy()

    # Only use years that passed the data-quality threshold.
    if "eligible_for_trend" in data.columns:
        data = data[data["eligible_for_trend"] == True]

    # Convert values to numeric and remove invalid observations.
    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data["annual_average"] = pd.to_numeric(
        data["annual_average"], errors="coerce"
    )

    data = data.dropna(subset=["year", "annual_average"])

    data = data[
        np.isfinite(data["year"]) &
        np.isfinite(data["annual_average"])
    ]

    data = data.sort_values("year")

    if data["year"].duplicated().any():
        raise ValueError("Duplicate years found in annual data.")

    if len(data) < 2:
        raise ValueError(
            "At least two eligible annual observations are required."
        )

    # Center the time variable at the first eligible year.
    # This makes the intercept easier to interpret and avoids
    # unnecessarily large intercept values.
    reference_year = int(data["year"].iloc[0])

    X = (
        data["year"].to_numpy(dtype=float) - reference_year
    ).reshape(-1, 1)

    y = data["annual_average"].to_numpy(dtype=float)

    # Fit the regression using all eligible observations.
    model = LinearRegression()
    model.fit(X, y)

    predictions = model.predict(X)

    return {
        "method": "linear_regression",
        "trend_direction": (
            "increasing" if model.coef_[0] > 0
            else "decreasing" if model.coef_[0] < 0
            else "stable"
        ),
        "slope_per_year": float(model.coef_[0]),
        "intercept_at_reference_year": float(model.intercept_),
        "reference_year": reference_year,
        "r_squared": float(model.score(X, y)),
        "years_analyzed": data["year"].astype(int).tolist(),
        "observed_values": y.tolist(),
        "fitted_values": predictions.tolist()
    }

def calculate_sens_slope(annual_data):
    """
    Calculate Sen's slope from annual environmental measurements.

    The slope is the median of all pairwise slopes between observations.

    Parameters:
        annual_data: DataFrame containing:
                     - year
                     - annual_average
                     - eligible_for_trend (optional)

    Returns:
        Dictionary containing Sen's slope, estimated intercept,
        trend direction, and fitted values.
    """

    required_columns = {"year", "annual_average"}

    if not required_columns.issubset(annual_data.columns):
        raise ValueError(
            "Data must contain year and annual_average columns."
        )

    if annual_data.empty:
        raise ValueError("No annual data was provided.")

    data = annual_data.copy()

    # Exclude years that failed the data-quality threshold.
    if "eligible_for_trend" in data.columns:
        data = data[data["eligible_for_trend"] == True]

    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data["annual_average"] = pd.to_numeric(
        data["annual_average"], errors="coerce"
    )

    data = data.dropna(subset=["year", "annual_average"])

    data = data[
        np.isfinite(data["year"]) &
        np.isfinite(data["annual_average"])
    ]

    data = data.sort_values("year")

    if data["year"].duplicated().any():
        raise ValueError("Duplicate years found in annual data.")

    if len(data) < 2:
        raise ValueError(
            "At least two eligible annual observations are required."
        )

    years = data["year"].to_numpy(dtype=float)
    values = data["annual_average"].to_numpy(dtype=float)

    # Calculate every pairwise slope.
    pairwise_slopes = []

    for i in range(len(years) - 1):
        slopes = (
            values[i + 1:] - values[i]
        ) / (
            years[i + 1:] - years[i]
        )

        pairwise_slopes.extend(slopes)

    # Sen's slope is the median of the pairwise slopes.
    sen_slope = float(np.median(pairwise_slopes))

    # Estimate the intercept at the first analyzed year.
    reference_year = int(years[0])

    intercept = float(
        np.median(
            values - sen_slope * (years - reference_year)
        )
    )

    # Calculate fitted values using the Sen's slope line.
    predictions = (
        intercept + sen_slope * (years - reference_year)
    )

    if sen_slope > 0:
        direction = "increasing"
    elif sen_slope < 0:
        direction = "decreasing"
    else:
        direction = "stable"

    return {
        "method": "sens_slope",
        "trend_direction": direction,
        "slope_per_year": sen_slope,
        "intercept_at_reference_year": intercept,
        "reference_year": reference_year,
        "years_analyzed": years.astype(int).tolist(),
        "observed_values": values.tolist(),
        "fitted_values": predictions.tolist()
    }
