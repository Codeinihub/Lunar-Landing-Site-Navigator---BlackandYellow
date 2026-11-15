from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from backend.schemas import PowerRequest

from backend.cache import initialize_cache

from backend.services import get_power_data

from backend.retrieval.power import DataRetrievalError


@asynccontextmanager
async def lifespan(app: FastAPI):

    initialize_cache()

    yield


app = FastAPI(
    title="Earth Trend Detective API",
    lifespan=lifespan
)


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
def power_endpoint(request: PowerRequest):

    try:

        return get_power_data(request)

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except DataRetrievalError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error)
        )