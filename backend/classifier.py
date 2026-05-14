import io
import logging
import os
from dataclasses import dataclass

from PIL import Image

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("PLANT_MODEL", "umucahit/PlantNet-300K")
_pipeline = None


@dataclass
class Prediction:
    species: str
    common_name: str
    confidence: float


def _load_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    # Import lazily so tests can mock before import
    from transformers import pipeline

    logger.info("Loading plant classifier model: %s", MODEL_NAME)
    device = _get_device()
    _pipeline = pipeline("image-classification", model=MODEL_NAME, device=device)
    logger.info("Model loaded on device: %s", device)
    return _pipeline


def _get_device() -> str:
    """Pick the best available compute device."""
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _label_to_names(label: str) -> tuple[str, str]:
    """Convert a model label to (species, common_name).

    PlantNet-300K labels are typically formatted as 'species_name' with
    underscores. Some models include a common name separated by ' - ' or '|'.
    """
    if " - " in label:
        parts = label.split(" - ", 1)
        species = parts[0].replace("_", " ").strip()
        common = parts[1].strip()
        return species, common
    if "|" in label:
        parts = label.split("|", 1)
        species = parts[0].replace("_", " ").strip()
        common = parts[1].strip()
        return species, common
    species = label.replace("_", " ").strip()
    return species, species


def predict(image_bytes: bytes, top_k: int = 3) -> list[Prediction]:
    """Run inference and return top_k predictions."""
    pipe = _load_pipeline()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    raw = pipe(image, top_k=top_k)  # type: ignore[call-arg]
    results: list[Prediction] = []
    for item in raw:
        species, common_name = _label_to_names(item["label"])
        results.append(
            Prediction(
                species=species,
                common_name=common_name,
                confidence=round(float(item["score"]), 4),
            )
        )
    return results
