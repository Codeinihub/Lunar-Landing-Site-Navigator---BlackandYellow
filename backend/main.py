
from contextlib import asynccontextmanager

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import Field

from backend.schemas import PowerRequest
from backend.cache import initialize_cache
from backend.services import get_power_data
from backend.retrieval.power import DataRetrievalError

from analysis.pipeline import analyze_annual_trends


# ==================================================
# 1. INITIALIZE BACKEND
# ==================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_cache()
    yield


app = FastAPI(
    title="Earth Trend Detective API",
    lifespan=lifespan
)


# ==================================================
# 2. CORS CONFIGURATION
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# 3. TREND ANALYSIS SETTINGS
# ==================================================

class TrendRequest(PowerRequest):

    min_completeness: float = Field(
        default=90.0,
        ge=0,
        le=100
    )

    alpha: float = Field(
        default=0.05,
        gt=0,
        lt=1
    )


# ==================================================
# 4. DATA CONVERSION HELPERS
# ==================================================

def dataframe_to_records(df):

    records = []

    for row in df.to_dict(orient="records"):

        converted = {}

        for key, value in row.items():

            if pd.isna(value):
                converted[key] = None

            elif hasattr(value, "isoformat"):
                converted[key] = value.isoformat()

            elif hasattr(value, "item"):
                converted[key] = value.item()

            else:
                converted[key] = value

        records.append(converted)

    return records


# ==================================================
# 5. PREPARE NASA POWER MEASUREMENTS
# ==================================================

def prepare_measurements(measurements, temporal_resolution):

    df = pd.DataFrame(measurements)

    if df.empty:
        raise ValueError(
            "No measurements were returned."
        )

    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(
            "NASA data is missing date or value columns."
        )

    # -----------------------------------
    # IDENTIFY NASA DATE FORMAT
    # -----------------------------------

    date_formats = {
        "monthly": "%Y%m",
        "daily": "%Y%m%d",
        "hourly": "%Y%m%d%H"
    }

    if temporal_resolution not in date_formats:

        raise ValueError(
            f"Unsupported temporal resolution: {temporal_resolution}"
        )

    df["date"] = df["date"].astype(str).str.strip()

    # -----------------------------------
    # REMOVE MONTHLY ANNUAL SUMMARIES
    # -----------------------------------

    if temporal_resolution == "monthly":

        valid_months = [
            f"{month:02d}"
            for month in range(1, 13)
        ]

        df = df[
            df["date"].str.fullmatch(r"\d{6}")
            & df["date"].str[-2:].isin(valid_months)
        ].copy()

    # -----------------------------------
    # PARSE DATES
    # -----------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        format=date_formats[temporal_resolution],
        errors="coerce"
    )

    # -----------------------------------
    # CONVERT MEASUREMENT VALUES
    # -----------------------------------

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce"
    )

    # NASA POWER missing data marker

    df["value"] = df["value"].replace(
        -999,
        float("nan")
    )

    # -----------------------------------
    # REMOVE INVALID DATES
    # -----------------------------------

    # Keep missing measurements so data
    # completeness can be calculated correctly.

    df = df.dropna(
        subset=["date"]
    )

    if df.empty or df["value"].notna().sum() == 0:

        raise ValueError(
            "No valid measurements are available."
        )

    df = df.sort_values(
        "date"
    ).reset_index(drop=True)

    return df


# ==================================================
# 6. DATA QUALITY CALCULATION
# ==================================================

def calculate_data_quality(df):

    total = len(df)

    valid = int(df["value"].notna().sum())

    missing = total - valid

    completeness = (
        (valid / total) * 100
        if total > 0
        else 0
    )

    return {
        "total_observations": total,
        "valid_observations": valid,
        "missing_observations": missing,
        "completeness_percent": round(
            completeness, 2
        )
    }


# ==================================================
# 7. ANNUAL DATA AGGREGATION
# ==================================================

def aggregate_annual(
    df,
    temporal_resolution,
    min_completeness
):

    data = df.copy()

    data["year"] = data["date"].dt.year

    annual_rows = []

    for year, group in data.groupby("year"):

        # -----------------------------------
        # EXPECTED MEASUREMENTS PER YEAR
        # -----------------------------------

        if temporal_resolution == "monthly":

            expected = 12

        elif temporal_resolution == "hourly":

            expected = (
                8784
                if pd.Timestamp(year=year).is_leap_year
                else 8760
            )

        else:

            expected = (
                366
                if pd.Timestamp(year=year).is_leap_year
                else 365
            )

        # -----------------------------------
        # VALID DATA
        # -----------------------------------

        valid_values = group["value"].dropna()

        valid_count = len(valid_values)

        completeness = (
            valid_count / expected
        ) * 100

        # -----------------------------------
        # ANNUAL AVERAGE
        # -----------------------------------

        annual_average = (
            float(valid_values.mean())
            if valid_count > 0
            else None
        )

        # -----------------------------------
        # STORE ANNUAL SUMMARY
        # -----------------------------------

        annual_rows.append({

            "year": int(year),

            "annual_average": annual_average,

            "valid_observations": valid_count,

            "expected_observations": expected,

            "completeness_percent": round(
                completeness,
                2
            ),

            "eligible_for_trend": (
                completeness >= min_completeness
                and annual_average is not None
            )

        })

    return pd.DataFrame(annual_rows)


# ==================================================
# 8. BASIC ENDPOINTS
# ==================================================

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


# ==================================================
# 9. NASA POWER DATA ENDPOINT
# ==================================================

@app.post("/data/powers")
def retrieve_power_data(request: PowerRequest):

    if request.start_year > request.end_year:

        raise HTTPException(
            status_code=400,
            detail="Start year must not exceed end year."
        )

    try:

        # -----------------------------------
        # RETRIEVE NASA POWER DATA
        # -----------------------------------

        raw_result = get_power_data(request)

        processed_data = {}

        for parameter, measurements in raw_result["data"].items():

            # Convert measurements using
            # the correct NASA timestamp format.

            df = prepare_measurements(
                measurements,
                request.temporal_resolution
            )

            # Calculate data quality

            quality = calculate_data_quality(df)

            processed_data[parameter] = {

                "measurements": dataframe_to_records(df),

                "quality": quality,

                "available_period": {
                    "start": df["date"].min().isoformat(),
                    "end": df["date"].max().isoformat()
                }

            }

        # -----------------------------------
        # RETURN DATA TO FRONTEND
        # -----------------------------------

        return {

            "source": raw_result["source"],

            "parameters": raw_result["parameters"],

            "location": {
                "latitude": raw_result["latitude"],
                "longitude": raw_result["longitude"]
            },

            "temporal_resolution": raw_result["temporal_resolution"],

            "requested_period": raw_result["period"],

            "data": processed_data

        }

    except DataRetrievalError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Data processing failed: {str(error)}"
        )


# ==================================================
# 10. COMPLETE ENVIRONMENTAL TREND ANALYSIS
# ==================================================

@app.post("/analysis/trends")
def analyze_trends(request: TrendRequest):

    if request.start_year > request.end_year:

        raise HTTPException(
            status_code=400,
            detail="Start year must not exceed end year."
        )

    try:

        # -----------------------------------
        # STEP 1: RETRIEVE NASA POWER DATA
        # -----------------------------------

        raw_result = get_power_data(request)

        analyzed_parameters = {}

        # -----------------------------------
        # STEP 2: PROCESS EACH PARAMETER
        # -----------------------------------

        for parameter, measurements in raw_result["data"].items():

            df = prepare_measurements(
                measurements,
                request.temporal_resolution
            )

            quality = calculate_data_quality(df)

            # -----------------------------------
            # STEP 3: AGGREGATE INTO ANNUAL DATA
            # -----------------------------------

            annual_df = aggregate_annual(
                df,
                temporal_resolution=request.temporal_resolution,
                min_completeness=request.min_completeness
            )

            # -----------------------------------
            # STEP 4: SELECT ELIGIBLE YEARS
            # -----------------------------------

            eligible_df = annual_df[
                annual_df["eligible_for_trend"]
            ].copy()

            if len(eligible_df) < 3:

                raise ValueError(
                    f"Not enough valid annual observations "
                    f"for {parameter}. At least 3 years "
                    f"with sufficient data are required."
                )

            # -----------------------------------
            # STEP 5: RUN STATISTICAL ANALYSIS
            # -----------------------------------

            trend_results = analyze_annual_trends(
                eligible_df,
                alpha=request.alpha
            )

            # -----------------------------------
            # STEP 6: PREPARE GRAPH DATA
            # -----------------------------------

            annual_records = dataframe_to_records(
                annual_df
            )

            analyzed_parameters[parameter] = {

                "quality": quality,

                "available_period": {

                    "start": df["date"].min().isoformat(),

                    "end": df["date"].max().isoformat()

                },

                "annual_data": annual_records,

                "trend_analysis": jsonable_encoder(
                    trend_results
                )

            }

        # -----------------------------------
        # STEP 7: RETURN RESULTS TO FRONTEND
        # -----------------------------------

        return {

            "source": raw_result["source"],

            "location": {

                "latitude": raw_result["latitude"],

                "longitude": raw_result["longitude"]

            },

            "temporal_resolution": raw_result["temporal_resolution"],

            "requested_period": raw_result["period"],

            "settings": {

                "min_completeness": request.min_completeness,

                "significance_level": request.alpha

            },

            "parameters": analyzed_parameters

        }

    except DataRetrievalError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Trend analysis failed: {str(error)}"
        )
