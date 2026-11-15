
import pandas as pd

from analysis.trends import (
    calculate_linear_regression,
    calculate_sens_slope
)


def test_linear_regression():
    print("\n===================================")
    print("TESTING LINEAR REGRESSION")
    print("===================================")

    # Test 1: Perfectly increasing trend.
    data = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023, 2024],
        "annual_average": [10, 12, 14, 16, 18],
        "eligible_for_trend": [True, True, True, True, True]
    })

    result = calculate_linear_regression(data)

    print("\nIncreasing trend:")
    print(result)

    assert result["trend_direction"] == "increasing"
    assert abs(result["slope_per_year"] - 2.0) < 1e-9
    assert abs(result["intercept_at_reference_year"] - 10.0) < 1e-9
    assert abs(result["r_squared"] - 1.0) < 1e-9

    # Test 2: Perfectly decreasing trend.
    data = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023, 2024],
        "annual_average": [20, 18, 16, 14, 12],
        "eligible_for_trend": [True, True, True, True, True]
    })

    result = calculate_linear_regression(data)

    print("\nDecreasing trend:")
    print(result)

    assert result["trend_direction"] == "decreasing"
    assert abs(result["slope_per_year"] - (-2.0)) < 1e-9

    # Test 3: Stable trend.
    data = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023],
        "annual_average": [15, 15, 15, 15],
        "eligible_for_trend": [True, True, True, True]
    })

    result = calculate_linear_regression(data)

    print("\nStable trend:")
    print(result)

    assert result["trend_direction"] == "stable"
    assert abs(result["slope_per_year"]) < 1e-9
    assert abs(result["r_squared"] - 1.0) < 1e-9

    # Test 4: Ineligible years should be excluded.
    data = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023],
        "annual_average": [10, 1000, 14, 16],
        "eligible_for_trend": [True, False, True, True]
    })

    result = calculate_linear_regression(data)

    print("\nExcluding ineligible year:")
    print(result)

    assert result["years_analyzed"] == [2020, 2022, 2023]
    assert abs(result["slope_per_year"] - 2.0) < 1e-9

    # Test 5: Insufficient eligible observations.
    data = pd.DataFrame({
        "year": [2020, 2021],
        "annual_average": [10, 12],
        "eligible_for_trend": [True, False]
    })

    try:
        calculate_linear_regression(data)
        assert False, "Expected ValueError was not raised."
    except ValueError:
        print("\nInsufficient data test passed.")

    print("\nAll linear regression tests passed!")


def test_sens_slope():
    print("\n===================================")
    print("TESTING SEN'S SLOPE")
    print("===================================")

    # Test 1: Perfectly increasing trend.
    data = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023, 2024],
        "annual_average": [10, 12, 14, 16, 18],
        "eligible_for_trend": [True, True, True, True, True]
    })

    result = calculate_sens_slope(data)

    print("\nIncreasing trend:")
    print(result)

    assert result["trend_direction"] == "increasing"
    assert abs(result["slope_per_year"] - 2.0) < 1e-9

    # Test 2: Perfectly decreasing trend.
    data = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023, 2024],
        "annual_average": [20, 18, 16, 14, 12],
        "eligible_for_trend": [True, True, True, True, True]
    })

    result = calculate_sens_slope(data)

    print("\nDecreasing trend:")
    print(result)

    assert result["trend_direction"] == "decreasing"
    assert abs(result["slope_per_year"] - (-2.0)) < 1e-9

    # Test 3: Stable trend.
    data = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023],
        "annual_average": [15, 15, 15, 15],
        "eligible_for_trend": [True, True, True, True]
    })

    result = calculate_sens_slope(data)

    print("\nStable trend:")
    print(result)

    assert result["trend_direction"] == "stable"
    assert abs(result["slope_per_year"]) < 1e-9

    # Test 4: An extreme observation should have limited influence.
    data = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023, 2024, 2025],
        "annual_average": [10, 12, 14, 16, 18, 1000],
        "eligible_for_trend": [True, True, True, True, True, True]
    })

    result = calculate_sens_slope(data)

    print("\nExtreme observation:")
    print(result)

    assert abs(result["slope_per_year"] - 2.0) < 1e-9

    # Test 5: Ineligible years should be excluded.
    data = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023],
        "annual_average": [10, 1000, 14, 16],
        "eligible_for_trend": [True, False, True, True]
    })

    result = calculate_sens_slope(data)

    print("\nExcluding ineligible year:")
    print(result)

    assert result["years_analyzed"] == [2020, 2022, 2023]
    assert abs(result["slope_per_year"] - 2.0) < 1e-9

    # Test 6: Insufficient eligible observations.
    data = pd.DataFrame({
        "year": [2020, 2021],
        "annual_average": [10, 12],
        "eligible_for_trend": [True, False]
    })

    try:
        calculate_sens_slope(data)
        assert False, "Expected ValueError was not raised."
    except ValueError:
        print("\nInsufficient data test passed.")

    print("\nAll Sen's slope tests passed!")


if __name__ == "__main__":
    test_linear_regression()
    test_sens_slope()

# if __name__ == "__main__":
#     test_linear_regression()
