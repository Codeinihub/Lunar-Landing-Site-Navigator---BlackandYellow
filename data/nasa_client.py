
import requests
from typing import Literal


NASA_POWER_BASE_URL = (
    "https://power.larc.nasa.gov/api/temporal"
)

TemporalResolution = Literal["daily", "monthly", "hourly"]


def fetch_power_data(
    latitude: float,
    longitude: float,
    start_year: int,
    end_year: int,
    parameters: list[str],
    temporal_resolution: TemporalResolution = "daily",
    community: str = "RE",
) -> dict:
    """
    Retrieve environmental measurements from NASA POWER.

    Returns a dictionary containing metadata and a separate
    list of date/value measurements for each parameter.
    """

    # 1. Validate inputs
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    if start_year > end_year:
        raise ValueError("Start year must not exceed end year.")

    if not parameters:
        raise ValueError("At least one parameter is required.")

    if temporal_resolution not in ("daily", "monthly", "hourly"):
        raise ValueError("Unsupported temporal resolution.")

    # 2. Construct NASA POWER endpoint
    url = (
        f"{NASA_POWER_BASE_URL}/"
        f"{temporal_resolution}/point"
    )

    # 3. Format dates
    if temporal_resolution == "monthly":
        start = str(start_year)
        end = str(end_year)
    else:
        start = f"{start_year}0101"
        end = f"{end_year}1231"

    # 4. Prepare request parameters
    params = {
        "parameters": ",".join(parameters),
        "community": community,
        "longitude": longitude,
        "latitude": latitude,
        "start": start,
        "end": end,
        "format": "JSON",
    }

    # 5. Request data from NASA
    try:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

    except requests.RequestException as error:
        raise RuntimeError(
            f"NASA POWER request failed: {error}"
        ) from error

    except ValueError as error:
        raise RuntimeError(
            "NASA POWER returned invalid JSON."
        ) from error

    # 6. Extract measurements
    try:
        measurements = result["properties"]["parameter"]

        data = {}

        for parameter in parameters:

            parameter_data = measurements[parameter]

            parameter_list = []

            for date, value in sorted(parameter_data.items()):

                parameter_list.append({
                    "date": date,
                    "value": None if value == -999 else value
                })

            if not any(
                item["value"] is not None
                for item in parameter_list
            ):
                raise ValueError(
                    f"No valid measurements for {parameter}."
                )

            data[parameter] = parameter_list

    except KeyError as error:
        raise RuntimeError(
            f"Unexpected NASA POWER response: missing {error}"
        ) from error

    # 7. Return structured data
    return {
        "source": "NASA POWER",
        "parameters": parameters,
        "latitude": latitude,
        "longitude": longitude,
        "temporal_resolution": temporal_resolution,
        "period": {
            "start": start_year,
            "end": end_year,
        },
        "data": data,
    }
