
import pandas as pd

from analysis.pipeline import analyze_annual_trends


def make_data(values, years=None):
    if years is None:
        years = list(range(2020, 2020 + len(values)))

    return pd.DataFrame({
        "year": years,
        "annual_average": values,
        "eligible_for_trend": [True] * len(values)
    })


def test_increasing_trend():
    result = analyze_annual_trends(
        make_data([10, 12, 14, 16, 18])
    )

    assert result["summary"]["observed_direction"] == "increasing"
    assert result["summary"]["is_significant"] is True

    assert result["methods"]["linear_regression"]["slope_per_year"] == 2.0
    assert result["methods"]["sens_slope"]["slope_per_year"] == 2.0

    assert result["years_analyzed"] == [2020, 2021, 2022, 2023, 2024]


def test_decreasing_trend():
    result = analyze_annual_trends(
        make_data([20, 18, 16, 14, 12])
    )

    assert result["summary"]["observed_direction"] == "decreasing"
    assert result["summary"]["is_significant"] is True


def test_excludes_ineligible_years():
    df = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023, 2024],
        "annual_average": [10, 1000, 12, 14, 16],
        "eligible_for_trend": [True, False, True, True, True]
    })

    result = analyze_annual_trends(df)

    assert result["years_analyzed"] == [2020, 2022, 2023, 2024]

    assert (
        result["methods"]["mann_kendall"]["years_analyzed"]
        == [2020, 2022, 2023, 2024]
    )


def test_insufficient_data():
    try:
        analyze_annual_trends(make_data([10, 12]))
        assert False, "Expected ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    print("TESTING UNIFIED TREND PIPELINE")

    test_increasing_trend()
    print("Increasing trend test passed.")

    test_decreasing_trend()
    print("Decreasing trend test passed.")

    test_excludes_ineligible_years()
    print("Ineligible years test passed.")

    test_insufficient_data()
    print("Insufficient data test passed.")

    print("\nAll trend pipeline tests passed!")
