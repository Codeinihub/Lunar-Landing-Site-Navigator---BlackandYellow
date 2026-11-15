from pydantic import BaseModel, Field
from typing import Literal


class PowerRequest(BaseModel):

    temporal_resolution: Literal[
        "daily",
        "monthly",
        "hourly"
    ]

    parameter: list[str] = Field(
        min_length=1
    )

    latitude: float = Field(
        ge=-90,
        le=90
    )

    longitude: float = Field(
        ge=-180,
        le=180
    )

    start_year: int = Field(
        ge=1981
    )

    end_year: int = Field(
        ge=1981
    )