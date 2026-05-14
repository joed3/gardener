from datetime import datetime

from pydantic import BaseModel


class Prediction(BaseModel):
    species: str
    common_name: str
    confidence: float


class IdentifyResponse(BaseModel):
    predictions: list[Prediction]


class GardenEntryCreate(BaseModel):
    species: str
    common_name: str
    confidence: float
    notes: str = ""
    captured_at: datetime
    latitude: float | None = None
    longitude: float | None = None


class GardenEntryResponse(BaseModel):
    id: int
    species: str
    common_name: str
    confidence: float
    image_url: str
    notes: str
    captured_at: datetime
    latitude: float | None
    longitude: float | None

    model_config = {"from_attributes": True}


class WikiSummary(BaseModel):
    title: str
    description: str | None = None
    extract: str | None = None
    thumbnail: dict | None = None
    content_urls: dict | None = None
