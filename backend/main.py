
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Earth Trend Detective API")


class PowerRequest(BaseModel):
    temporal_resolution: Literal["daily", "monthly", "hourly"] = "daily"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=-180)
    start_year: int
    end_year: int
    parameter: list[str] = Field(min_length=1, max_length=20)


@app.get("/")
def home():
    return {"message": "Earth Trend Detective API is running!"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/data/power")
def get_power_data(request: PowerRequest):

    if request.start_year > request.end_year:
        raise HTTPException(
            status_code=400,
            detail="Start year must be before end year"
        )

    url = (f"https://power.larc.nasa.gov/api/temporal/{requests.temporal_resolution}/point")

    params = {
        "parameters": ",".join(request.parameter),
        "community": "RE",
        "longitude": request.longitude,
        "latitude": request.latitude,
        "start": f"{request.start_year}0101",
        "end": f"{request.end_year}1231",
        "format": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        # Extract the requested environmental measurements
        measurements = result["properties"]["parameter"][
            request.parameter
        ]

        # Convert NASA's date/value dictionary into a list
        data = []

        for date, value in sorted(measurements.items()):
            data.append({
                "date": date,
                "value": None if value == -999 else value
            })

        return {
            "source": "NASA POWER",
            "parameter": request.parameter,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "data": data
        }

    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"NASA POWER request failed: {str(error)}"
        )

    except (KeyError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Unexpected response format from NASA POWER"
        )





