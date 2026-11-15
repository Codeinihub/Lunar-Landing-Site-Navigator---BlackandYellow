import requests

from backend.schemas import PowerRequest


NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/"
)


class DataRetrievalError(Exception):
    pass


def fetch_power_data(request: PowerRequest):

    if request.start_year > request.end_year:

        raise ValueError(
            "Start year must be before end year"
        )

    url = (
        f"{NASA_POWER_URL}"
        f"{request.temporal_resolution}/point"
    )

    if request.temporal_resolution == "monthly":

        start = str(request.start_year)
        end = str(request.end_year)

    else:

        start = f"{request.start_year}0101"
        end = f"{request.end_year}1231"

    params = {

        "parameters": ",".join(request.parameter),

        "community": "RE",

        "longitude": request.longitude,

        "latitude": request.latitude,

        "start": start,

        "end": end,

        "format": "JSON"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        measurements = result[
            "properties"
        ][
            "parameter"
        ]

        data = {}

        for parameter in request.parameter:

            parameter_data = measurements[parameter]

            parameter_list = []

            for date, value in sorted(
                parameter_data.items()
            ):

                parameter_list.append({

                    "date": date,

                    "value": (
                        None if value == -999 else value
                    )

                })

            if not any(
                item["value"] is not None
                for item in parameter_list
            ):

                raise DataRetrievalError(
                    f"No valid measurements for {parameter}"
                )

            data[parameter] = parameter_list

        return {

            "source": "NASA POWER",

            "parameters": request.parameter,

            "latitude": request.latitude,

            "longitude": request.longitude,

            "period": {

                "start": request.start_year,

                "end": request.end_year

            },

            "data": data

        }

    except requests.RequestException as error:

        raise DataRetrievalError(
            f"NASA POWER request failed: {error}"
        ) from error

    except (KeyError, TypeError, ValueError) as error:

        raise DataRetrievalError(
            "Unexpected response format from NASA POWER"
        ) from error