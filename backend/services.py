from backend.cache import get_or_fetch_data
from backend.retrieval.power import fetch_power_data

from backend.schemas import PowerRequest


def get_power_data(request: PowerRequest):

    return get_or_fetch_data(

        namespace="nasa_power",

        parameters=request.model_dump(),

        fetch_function=lambda: fetch_power_data(request),

        max_age=604800

    )