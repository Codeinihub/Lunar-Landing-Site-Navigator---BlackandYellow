
"""Retrieve and normalize NASA POWER point measurements for Earth Detective."""

import math
from datetime import date, timedelta

import requests

from backend.schemas import PowerRequest


# ===================================
# NASA POWER CONFIGURATION
# ===================================

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/"
REQUEST_TIMEOUT_SECONDS = 60

# Conservative buffer for near-real-time daily/hourly measurements.
# NASA's actual latest available date can vary by data product.
RECENT_DATA_BUFFER_DAYS = 10


# ===================================
# CUSTOM ERROR
# ===================================

class DataRetrievalError(Exception):
    pass


# ===================================
# CLEAN NASA MEASUREMENTS
# ===================================

def clean_measurement(value):
    """Return a finite float, or None for missing/invalid NASA values."""
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number) or number == -999:
        return None

    return number


# ===================================
# BUILD VALID REQUEST DATES
# ===================================

def get_request_dates(request: PowerRequest):
    """Return dates in the format required by NASA POWER's temporal API."""
    resolution = request.temporal_resolution
    today = date.today()

    if request.start_year > request.end_year:
        raise ValueError("Start year must be before or equal to end year.")

    if request.end_year > today.year:
        raise ValueError("NASA POWER historical requests cannot end in a future year.")

    if resolution == "hourly" and request.start_year < 2001:
        raise ValueError("NASA POWER hourly data starts in 2001.")

    if resolution == "monthly":
        # NASA POWER monthly temporal API accepts YYYY.
        return str(request.start_year), str(request.end_year)

    if resolution not in ("daily", "hourly"):
        raise ValueError(f"Unsupported temporal resolution: {resolution}")

    start_date = date(request.start_year, 1, 1)
    end_date = date(request.end_year, 12, 31)

    # Avoid dates NASA cannot yet have measured when requesting this year.
    # The buffer is conservative, not a guarantee of availability.
    if request.end_year == today.year:
        end_date = min(end_date, today - timedelta(days=RECENT_DATA_BUFFER_DAYS))

    if end_date < start_date:
        raise ValueError("No daily/hourly measurements are available in this date range yet.")

    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")


# ===================================
# EXTRACT NASA ERROR INFORMATION
# ===================================

def nasa_error_details(response):
    """Return a short, useful explanation for a rejected NASA request."""
    try:
        payload = response.json()
        if isinstance(payload, dict):
            message = payload.get("messages") or payload.get("errors") or payload.get("detail")
            if message:
                return str(message)[:500]
    except ValueError:
        pass

    return (response.text or "No error details supplied")[:500]


# ===================================
# FETCH NASA POWER DATA
# ===================================

def fetch_power_data(request: PowerRequest):
    resolution = request.temporal_resolution
    url = f"{NASA_POWER_URL}{resolution}/point"
    start, end = get_request_dates(request)

    params = {
        "parameters": ",".join(request.parameter),
        "community": "RE",
        "longitude": request.longitude,
        "latitude": request.latitude,
        "start": start,
        "end": end,
        "format": "JSON",
    }

    print("\n========== NASA POWER DEBUG ==========")
    print("Request URL:", url)
    print("Temporal resolution:", resolution)
    print("Parameters:", request.parameter)
    print("Latitude:", request.latitude)
    print("Longitude:", request.longitude)
    print("Start:", start)
    print("End:", end)

    try:
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as error:
        print("NASA REQUEST ERROR:", str(error))
        raise DataRetrievalError(
            f"Could not connect to NASA POWER: {error}"
        ) from error

    print("NASA HTTP status:", response.status_code)

    if not response.ok:
        detail = nasa_error_details(response)
        print("NASA ERROR DETAILS:", detail)
        raise DataRetrievalError(
            f"NASA POWER returned HTTP {response.status_code}: {detail}"
        )

    try:
        result = response.json()
    except ValueError as error:
        raise DataRetrievalError(
            "NASA POWER returned an invalid JSON response."
        ) from error

    try:
        measurements = result["properties"]["parameter"]
    except (KeyError, TypeError) as error:
        print("Unexpected NASA response:", str(result)[:500])
        raise DataRetrievalError(
            "Unexpected response format from NASA POWER."
        ) from error

    if not isinstance(measurements, dict):
        raise DataRetrievalError(
            "NASA POWER returned an invalid measurement structure."
        )

    print("Returned parameters:", list(measurements.keys()))
    data = {}

    for parameter in request.parameter:
        print("\nProcessing parameter:", parameter)

        if parameter not in measurements:
            raise DataRetrievalError(
                f"NASA POWER did not return '{parameter}'. "
                f"Available parameters: {list(measurements.keys())}"
            )

        parameter_data = measurements[parameter]
        if not isinstance(parameter_data, dict):
            raise DataRetrievalError(
                f"Invalid measurement data for {parameter}."
            )

        print("Total raw measurements:", len(parameter_data))
        print("First five raw measurements:", list(parameter_data.items())[:5])

        parameter_list = []
        valid_count = 0
        missing_count = 0

        for timestamp, value in sorted(parameter_data.items()):
            cleaned_value = clean_measurement(value)
            if cleaned_value is None:
                missing_count += 1
            else:
                valid_count += 1

            parameter_list.append({
                "date": str(timestamp),
                "value": cleaned_value,
            })

        print("Valid measurements:", valid_count)
        print("Missing measurements:", missing_count)
        print("First five cleaned measurements:", parameter_list[:5])

        if valid_count == 0:
            raise DataRetrievalError(
                f"No valid measurements for {parameter}. NASA returned "
                f"{len(parameter_list)} measurements, but none were usable. "
                "Check the requested location, parameter, and date range."
            )

        data[parameter] = parameter_list
        print(f"Successfully processed {parameter}")

    final_result = {
        "source": "NASA POWER",
        "temporal_resolution": resolution,
        "parameters": request.parameter,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "period": {
            "start": request.start_year,
            "end": request.end_year,
        },
        "data": data,
    }

    print("\nNASA POWER retrieval successful.")
    print("Processed parameters:", list(data.keys()))
    print("========== NASA POWER DEBUG END ==========\n")

    return final_result
