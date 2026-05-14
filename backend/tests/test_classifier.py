from unittest.mock import MagicMock, patch

import pytest

import classifier


def test_label_to_names_plain():
    species, common = classifier._label_to_names("Monstera_deliciosa")
    assert species == "Monstera deliciosa"
    assert common == "Monstera deliciosa"


def test_label_to_names_dash_separator():
    species, common = classifier._label_to_names("Monstera_deliciosa - Swiss Cheese Plant")
    assert species == "Monstera deliciosa"
    assert common == "Swiss Cheese Plant"


def test_label_to_names_pipe_separator():
    species, common = classifier._label_to_names("Rosa_canina|Dog Rose")
    assert species == "Rosa canina"
    assert common == "Dog Rose"


def test_predict_returns_predictions():
    import io

    from PIL import Image as PILImage

    buf = io.BytesIO()
    img = PILImage.new("RGB", (224, 224), color=(0, 128, 0))
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    mock_pipeline = MagicMock()
    mock_pipeline.return_value = [
        {"label": "Monstera_deliciosa - Swiss Cheese Plant", "score": 0.91},
        {"label": "Monstera_adansonii", "score": 0.06},
        {"label": "Rhaphidophora_tetrasperma", "score": 0.02},
    ]

    with patch("classifier._pipeline", mock_pipeline):
        results = classifier.predict(image_bytes, top_k=3)

    assert len(results) == 3
    assert results[0].species == "Monstera deliciosa"
    assert results[0].common_name == "Swiss Cheese Plant"
    assert results[0].confidence == 0.91
    assert results[1].species == "Monstera adansonii"


def test_predict_empty_image_raises():
    from PIL import UnidentifiedImageError

    with pytest.raises((UnidentifiedImageError, OSError)):
        classifier.predict(b"", top_k=3)
