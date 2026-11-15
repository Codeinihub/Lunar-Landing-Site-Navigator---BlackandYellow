
from fastapi import FastAPI, HTTPException

from backend.schemas import PowerRequest
from backend.retrival import fetch_power_data


from backend.cache import (
    initialize_cache,
    get_or_fetch_data
)


initialize_cache()

app = FastAPI(title="Earth Trend Detective API")


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


@app.post("/data/power")
def get_power_data(request: PowerRequest):

    data = get_or_fetch_data(
        namespace="nasa_power",
        parameters=request.model_dump(),
        fetch_function=lambda: fetch_power_data(request)
    )

    return data

