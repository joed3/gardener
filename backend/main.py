import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
from sqlalchemy.orm import Session

import classifier
import wiki
from database import GardenEntry, create_tables, get_db
from models import GardenEntryCreate, GardenEntryResponse, IdentifyResponse, WikiSummary

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="Gardener API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/identify", response_model=IdentifyResponse)
async def identify(image: UploadFile = File(...)):
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file")

    predictions_raw = classifier.predict(contents)
    predictions = [
        {
            "species": p.species,
            "common_name": p.common_name,
            "confidence": p.confidence,
        }
        for p in predictions_raw
    ]
    return {"predictions": predictions}


@app.get("/wiki/{species_name}", response_model=WikiSummary | None)
async def get_wiki(species_name: str, common_name: str | None = None):
    summary = await wiki.get_summary(species_name, common_name)
    return summary


@app.post("/garden", response_model=dict)
async def save_to_garden(
    entry: GardenEntryCreate,
    db: Session = Depends(get_db),
):
    db_entry = GardenEntry(
        species=entry.species,
        common_name=entry.common_name,
        confidence=entry.confidence,
        image_path="",
        notes=entry.notes,
        captured_at=entry.captured_at,
        latitude=entry.latitude,
        longitude=entry.longitude,
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return {"id": db_entry.id}


@app.post("/garden/upload")
async def upload_garden_image(image: UploadFile = File(...)):
    """Upload an image and return the stored filename."""
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file")

    ext = Path(image.filename or "image.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOADS_DIR / filename
    dest.write_bytes(contents)

    captured_at = _extract_exif_datetime(contents)
    return {
        "image_url": f"/uploads/{filename}",
        "captured_at": captured_at.isoformat() if captured_at else None,
    }


@app.patch("/garden/{entry_id}/image")
async def attach_image(
    entry_id: int,
    image_url: str,
    db: Session = Depends(get_db),
):
    entry = db.get(GardenEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry.image_path = image_url.lstrip("/")
    db.commit()
    return {"ok": True}


@app.get("/garden", response_model=list[GardenEntryResponse])
def list_garden(db: Session = Depends(get_db)):
    entries = db.query(GardenEntry).order_by(GardenEntry.captured_at.desc()).all()
    return [_entry_to_response(e) for e in entries]


@app.get("/garden/{entry_id}", response_model=GardenEntryResponse)
def get_garden_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(GardenEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return _entry_to_response(entry)


def _entry_to_response(entry: GardenEntry) -> GardenEntryResponse:
    image_url = f"/{entry.image_path}" if entry.image_path else ""
    return GardenEntryResponse(
        id=entry.id,
        species=entry.species,
        common_name=entry.common_name,
        confidence=entry.confidence,
        image_url=image_url,
        notes=entry.notes or "",
        captured_at=entry.captured_at,
        latitude=entry.latitude,
        longitude=entry.longitude,
    )


def _extract_exif_datetime(image_bytes: bytes) -> datetime | None:
    try:
        img = PILImage.open(__import__("io").BytesIO(image_bytes))
        exif_data = img._getexif()  # type: ignore[attr-defined]
        if not exif_data:
            return None
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None
