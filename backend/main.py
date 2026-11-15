
import requests
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Earth Trend Detective API")

# class PowerRequest(BaseModel):
#     temporal_resolution: Literal["daily", "monthly", "hourly"] = "daily"

#     latitude: float = Field(ge=-90, le=90)
#     longitude: float = Field(ge=-180, le=180)

#     start_year: int
#     end_year: int

#     parameter: list[str] = Field(min_length=1, max_length=20)


# @app.get("/")
# def home():
#     return {"message": "Earth Trend Detective API is running!"}


# @app.get("/health")
# def health():
#     return {"status": "healthy"}


# @app.post("/data/powers")
# def get_power_data(request: PowerRequest):

#     if request.start_year > request.end_year:
#         raise HTTPException(
#             status_code=400,
#             detail="Start year must be before end year"
#         )

#     url = (
#         f"https://power.larc.nasa.gov/api/temporal/"
#         f"{request.temporal_resolution}/point"
#     )

#     if request.temporal_resolution == "monthly":
#         start = str(request.start_year)
#         end = str(request.end_year)

#     else:
#         start = f"{request.start_year}0101"
#         end = f"{request.end_year}1231"

#     params = {
#         "parameters": ",".join(request.parameter),
#         "community": "RE",
#         "longitude": request.longitude,
#         "latitude": request.latitude,
#         "start": start,
#         "end": end,
#         "format": "JSON"
#     }

#     try:
#         response = requests.get(url, params=params, timeout=30)
#         response.raise_for_status()

#         result = response.json()

#         measurements = result["properties"]["parameter"]

#         data = {}

#         for parameter in request.parameter:

#             parameter_data = measurements[parameter]

#             parameter_list = []

#             for date, value in sorted(parameter_data.items()):
#                 parameter_list.append({
#                     "date": date,
#                     "value": None if value == -999 else value
#                 })

#             if not any(
#                 item["value"] is not None
#                 for item in parameter_list
#             ):
#                 raise HTTPException(
#                     status_code=404,
#                     detail=f"No valid measurements for {parameter}"
#                 )

#             data[parameter] = parameter_list

#         return {
#             "source": "NASA POWER",
#             "parameters": request.parameter,
#             "latitude": request.latitude,
#             "longitude": request.longitude,
#             "period": {
#                 "start": request.start_year,
#                 "end": request.end_year
#             },
#             "data": data
#         }

#     except requests.RequestException as error:
#         raise HTTPException(
#             status_code=502,
#             detail=f"NASA POWER request failed: {str(error)}"
#         )

#     except (KeyError, ValueError):
#         raise HTTPException(
#             status_code=502,
#             detail="Unexpected response format from NASA POWER"
#         )

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import Literal
import pandas as pd

from data.nasa_client import fetch_power_data
from data.preprocessing import preprocess_data, get_data_quality, aggregate_annual

# --------------------------------------------------
# 1. Initialize FastAPI
# --------------------------------------------------

app = FastAPI(title="Earth Trend Detective API")


# --------------------------------------------------
# 2. Configure CORS for frontend integration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to frontend origins before production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# 3. Define request schema
# --------------------------------------------------

class PowerRequest(BaseModel):

    temporal_resolution: Literal[
        "daily", "monthly", "hourly"
    ] = "daily"

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    start_year: int = Field(ge=1981)
    end_year: int = Field(ge=1981)

    parameter: list[str] = Field(
        min_length=1,
        max_length=20
    )


# --------------------------------------------------
# 4. Helper function to convert DataFrame to JSON
# --------------------------------------------------

def dataframe_to_records(df):

    records = []

    for row in df.itertuples(index=False):

        date = row.date
        value = row.value

        records.append({
            "date": (
                date.isoformat()
                if pd.notna(date)
                else None
            ),
            "value": (
                None
                if pd.isna(value)
                else float(value)
            )
        })

    return records


# --------------------------------------------------
# 5. Basic endpoints
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "Earth Trend Detective API is running!"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# --------------------------------------------------
# 6. NASA POWER + Preprocessing endpoint
# --------------------------------------------------

@app.post("/data/powers")
def get_power_data(request: PowerRequest):

    # Validate date range
    if request.start_year > request.end_year:

        raise HTTPException(
            status_code=400,
            detail="Start year must not exceed end year."
        )

    try:

        # STEP 1: Retrieve NASA POWER data
        raw_result = fetch_power_data(
            latitude=request.latitude,
            longitude=request.longitude,
            start_year=request.start_year,
            end_year=request.end_year,
            parameters=request.parameter,
            temporal_resolution=request.temporal_resolution,
            community="RE"
        )

        # STEP 2: Process each requested parameter
        processed_data = {}

        for parameter, measurements in raw_result["data"].items():

            # Clean the measurements
            df = preprocess_data(measurements)

            # Calculate data quality
            quality = get_data_quality(df)

            # Store processed results
            processed_data[parameter] = {
                "measurements": dataframe_to_records(df),
                "quality": jsonable_encoder(quality)
            }

        # STEP 3: Return everything to the frontend
        return {
            "source": raw_result["source"],
            "parameters": raw_result["parameters"],
            "latitude": raw_result["latitude"],
            "longitude": raw_result["longitude"],
            "temporal_resolution": raw_result["temporal_resolution"],
            "period": raw_result["period"],
            "data": processed_data
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error)
        )
