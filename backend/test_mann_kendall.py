
import pandas as pd

from analysis.correlation import calculate_mann_kendall


def make_data(values, years=None):
    if years is None:
        years = list(range(2020, 2020 + len(values)))

    return pd.DataFrame({
        "year": years,
        "annual_average": values
    })


def test_increasing():
    result = calculate_mann_kendall(
        make_data([10, 12, 14, 16, 18])
    )

    assert result["trend_direction"] == "increasing"
    assert result["s_statistic"] == 10
    assert result["is_significant"] is True


def test_decreasing():
    result = calculate_mann_kendall(
        make_data([20, 18, 16, 14, 12])
    )

    assert result["trend_direction"] == "decreasing"
    assert result["s_statistic"] == -10
    assert result["is_significant"] is True


def test_stable():
    result = calculate_mann_kendall(
        make_data([15, 15, 15, 15, 15])
    )

    assert result["trend_direction"] == "no_significant_trend"
    assert result["s_statistic"] == 0
    assert result["is_significant"] is False


def test_tied_values():
    result = calculate_mann_kendall(
        make_data([10, 10, 12, 12, 14])
    )

    assert result["s_statistic"] > 0
    assert result["variance_s"] > 0

    # Positive S indicates an upward tendency,
    # but the trend is not statistically significant.
    assert result["trend_direction"] == "no_significant_trend"
    assert result["observed_direction"] == "increasing"
    assert result["is_significant"] is False

    print("\nTied values test:")
    print(result)


def test_excludes_ineligible_years():
    df = pd.DataFrame({
        "year": [2020, 2021, 2022, 2023, 2024],
        "annual_average": [10, 1000, 12, 14, 16],
        "eligible_for_trend": [True, False, True, True, True]
    })

    result = calculate_mann_kendall(df)

    assert result["years_analyzed"] == [2020, 2022, 2023, 2024]

    # The observations have an upward tendency,
    # but four observations aren't enough for significance here.
    assert result["s_statistic"] > 0
    assert result["trend_direction"] == "no_significant_trend"
    assert result["observed_direction"] == "increasing"
    assert result["is_significant"] is False

    print("\nIneligible years test:")
    print(result)


def test_insufficient_data():
    try:
        calculate_mann_kendall(make_data([10, 12]))
        assert False, "Expected ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    print("TESTING MANN-KENDALL")

    test_increasing()
    test_decreasing()
    test_stable()
    test_tied_values()
    test_excludes_ineligible_years()
    test_insufficient_data()

    print("All Mann-Kendall tests passed!")
