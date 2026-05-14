import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import classifier
from database import Base, get_db


def _make_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    img = PILImage.new("RGB", (100, 100), color=(34, 139, 34))
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture()
def client():
    # StaticPool ensures every SQLAlchemy connection hits the same in-memory DB
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    from main import app

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_identify(client):
    mock_predictions = [
        classifier.Prediction("Monstera deliciosa", "Swiss Cheese Plant", 0.91),
        classifier.Prediction("Monstera adansonii", "Monkey Mask", 0.06),
    ]
    with patch("main.classifier.predict", return_value=mock_predictions):
        response = client.post(
            "/identify",
            files={"image": ("plant.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["predictions"]) == 2
    assert data["predictions"][0]["species"] == "Monstera deliciosa"
    assert data["predictions"][0]["confidence"] == 0.91


def test_identify_empty_file(client):
    response = client.post(
        "/identify",
        files={"image": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_garden_post_and_get(client):
    payload = {
        "species": "Rosa canina",
        "common_name": "Dog Rose",
        "confidence": 0.85,
        "notes": "Spotted near the hedge",
        "captured_at": "2026-05-14T10:00:00Z",
        "latitude": 51.5,
        "longitude": -0.1,
    }
    post_response = client.post("/garden", json=payload)
    assert post_response.status_code == 200
    entry_id = post_response.json()["id"]
    assert isinstance(entry_id, int)

    get_response = client.get("/garden")
    assert get_response.status_code == 200
    entries = get_response.json()
    assert len(entries) == 1
    assert entries[0]["species"] == "Rosa canina"
    assert entries[0]["latitude"] == 51.5


def test_garden_get_by_id(client):
    payload = {
        "species": "Hedera helix",
        "common_name": "English Ivy",
        "confidence": 0.78,
        "notes": "",
        "captured_at": "2026-05-14T11:00:00Z",
        "latitude": None,
        "longitude": None,
    }
    post = client.post("/garden", json=payload)
    entry_id = post.json()["id"]

    get = client.get(f"/garden/{entry_id}")
    assert get.status_code == 200
    assert get.json()["species"] == "Hedera helix"


def test_garden_get_not_found(client):
    response = client.get("/garden/99999")
    assert response.status_code == 404


def test_wiki_endpoint(client):
    mock_summary = {
        "title": "Monstera deliciosa",
        "description": "Species of plant",
        "extract": "Long description...",
        "thumbnail": None,
        "content_urls": None,
    }
    with patch("main.wiki.get_summary", return_value=mock_summary):
        response = client.get("/wiki/Monstera deliciosa")

    assert response.status_code == 200
    assert response.json()["title"] == "Monstera deliciosa"


def test_wiki_not_found_returns_null(client):
    with patch("main.wiki.get_summary", return_value=None):
        response = client.get("/wiki/Unknown species xyz")

    assert response.status_code == 200
    assert response.json() is None
