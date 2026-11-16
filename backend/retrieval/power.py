
import math
import requests

from backend.schemas import PowerRequest


# ===================================
# NASA POWER CONFIGURATION
# ===================================

NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/"
)


# ===================================
# CUSTOM ERROR
# ===================================

class DataRetrievalError(Exception):
    pass


# ===================================
# CLEAN NASA MEASUREMENTS
# ===================================

def clean_measurement(value):
    """
    Convert NASA POWER values into valid numbers.

    NASA uses -999 for missing measurements.
    Missing or invalid values become None.
    """

    if value is None:
        return None

    try:
        number = float(value)

    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    if number == -999:
        return None

    return number


# ===================================
# FETCH NASA POWER DATA
# ===================================

def fetch_power_data(request: PowerRequest):

    # -----------------------------------
    # VALIDATE YEAR RANGE
    # -----------------------------------

    if request.start_year > request.end_year:

        raise ValueError(
            "Start year must be before or equal to end year."
        )

    # -----------------------------------
    # BUILD NASA POWER URL
    # -----------------------------------

    resolution = request.temporal_resolution

    url = (
        f"{NASA_POWER_URL}"
        f"{resolution}/point"
    )

    # NASA POWER historical monthly API
    # uses YYYY.
    #
    # Daily and hourly APIs use YYYYMMDD.

    if resolution == "monthly":

        start = str(request.start_year)
        end = str(request.end_year)

    else:

        start = f"{request.start_year}0101"
        end = f"{request.end_year}1231"

    # -----------------------------------
    # BUILD API PARAMETERS
    # -----------------------------------

    params = {

        "parameters": ",".join(request.parameter),

        "community": "RE",

        "longitude": request.longitude,

        "latitude": request.latitude,

        "start": start,

        "end": end,

        "format": "JSON"

    }

    # -----------------------------------
    # DEBUG REQUEST INFORMATION
    # -----------------------------------

    print("\n========== NASA POWER DEBUG ==========")

    print("Request URL:", url)

    print("Temporal resolution:", resolution)

    print("Parameters:", request.parameter)

    print("Latitude:", request.latitude)

    print("Longitude:", request.longitude)

    print("Start:", start)

    print("End:", end)

    # -----------------------------------
    # SEND REQUEST TO NASA
    # -----------------------------------

    try:

        response = requests.get(
            url,
            params=params,
            timeout=60
        )

        print("NASA HTTP status:", response.status_code)

        response.raise_for_status()

    except requests.RequestException as error:

        print("NASA REQUEST ERROR:", str(error))

        raise DataRetrievalError(
            f"NASA POWER request failed: {error}"
        ) from error

    # -----------------------------------
    # CONVERT RESPONSE TO JSON
    # -----------------------------------

    try:

        result = response.json()

    except ValueError as error:

        print("NASA returned invalid JSON.")

        raise DataRetrievalError(
            "NASA POWER returned an invalid JSON response."
        ) from error

    # -----------------------------------
    # READ NASA RESPONSE
    # -----------------------------------

    try:

        measurements = result[
            "properties"
        ][
            "parameter"
        ]

    except (KeyError, TypeError) as error:

        print("Unexpected NASA response structure.")

        if isinstance(result, dict):

            print(
                "Response keys:",
                list(result.keys())
            )

            print(
                "NASA messages:",
                result.get("messages", [])
            )

        raise DataRetrievalError(
            "Unexpected response format from NASA POWER."
        ) from error

    if not isinstance(measurements, dict):

        raise DataRetrievalError(
            "NASA POWER returned an invalid measurement structure."
        )

    print(
        "Returned parameters:",
        list(measurements.keys())
    )

    # -----------------------------------
    # PROCESS EACH PARAMETER
    # -----------------------------------

    data = {}

    for parameter in request.parameter:

        print("\nProcessing parameter:", parameter)

        # Check whether NASA returned the parameter

        if parameter not in measurements:

            raise DataRetrievalError(
                f"NASA POWER did not return parameter "
                f"'{parameter}'. Available parameters: "
                f"{list(measurements.keys())}"
            )

        parameter_data = measurements[parameter]

        if not isinstance(parameter_data, dict):

            raise DataRetrievalError(
                f"Invalid measurement data for {parameter}."
            )

        print(
            "Total raw measurements:",
            len(parameter_data)
        )

        print(
            "First five raw measurements:",
            list(parameter_data.items())[:5]
        )

        # -----------------------------------
        # CLEAN MEASUREMENTS
        # -----------------------------------

        parameter_list = []

        valid_count = 0

        missing_count = 0

        for date, value in sorted(
            parameter_data.items()
        ):

            cleaned_value = clean_measurement(value)

            if cleaned_value is None:

                missing_count += 1

            else:

                valid_count += 1

            parameter_list.append({

                "date": str(date),

                "value": cleaned_value

            })

        # -----------------------------------
        # DEBUG MEASUREMENT QUALITY
        # -----------------------------------

        print(
            "Valid measurements:",
            valid_count
        )

        print(
            "Missing measurements:",
            missing_count
        )

        print(
            "First five cleaned measurements:",
            parameter_list[:5]
        )

        # -----------------------------------
        # HANDLE EMPTY DATA
        # -----------------------------------

        if valid_count == 0:

            print(
                "NASA POWER ERROR:",
                f"No valid measurements for {parameter}"
            )

            print(
                "NASA messages:",
                result.get("messages", [])
            )

            print(
                "NASA POWER DEBUG END"
            )

            raise DataRetrievalError(
                f"No valid measurements for {parameter}. "
                f"NASA returned {len(parameter_list)} "
                f"measurements, but none contained "
                f"usable values. Check the requested "
                f"location, parameter, and date range."
            )

        # Store cleaned measurements

        data[parameter] = parameter_list

        print(
            f"Successfully processed {parameter}"
        )

    # -----------------------------------
    # BUILD FINAL BACKEND RESPONSE
    # -----------------------------------

    final_result = {

        "source": "NASA POWER",

        "temporal_resolution": resolution,

        "parameters": request.parameter,

        "latitude": request.latitude,

        "longitude": request.longitude,

        "period": {

            "start": request.start_year,

            "end": request.end_year

        },

        "data": data

    }

    print("\nNASA POWER retrieval successful.")

    print(
        "Processed parameters:",
        list(data.keys())
    )

    print("========== NASA POWER DEBUG END ==========\n")

    return final_result
