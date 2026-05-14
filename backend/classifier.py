import io
import json
import logging
import os
import tarfile
from dataclasses import dataclass
from pathlib import Path

import httpx
import timm
import timm.data
import torch
from PIL import Image

logger = logging.getLogger(__name__)

MODEL_REPO = os.getenv(
    "PLANT_MODEL_REPO",
    "hf_hub:timm/eva02_large_patch14_clip_336.merged2b_ft_inat21",
)
INAT_CACHE_DIR = Path(os.getenv("INAT_CACHE_DIR", str(Path.home() / ".cache" / "inat21")))
NUM_CLASSES = 10_000

_INAT21_VAL_URL = (
    "https://ml-inat-competition-datasets.s3.amazonaws.com/2021/val.json.tar.gz"
)

_model = None
_transform = None
_idx_to_species: dict[int, tuple[str, str]] = {}
_device: torch.device | None = None


@dataclass
class Prediction:
    species: str
    common_name: str
    confidence: float


def _get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _download_inat21_categories() -> list[dict]:
    INAT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cats_path = INAT_CACHE_DIR / "categories.json"
    if cats_path.exists():
        return json.loads(cats_path.read_text())

    tar_path = INAT_CACHE_DIR / "val.json.tar.gz"
    logger.info("Downloading iNat2021 categories (one-time, ~10 MB)…")
    with httpx.stream("GET", _INAT21_VAL_URL, follow_redirects=True, timeout=300.0) as resp:
        resp.raise_for_status()
        with tar_path.open("wb") as fh:
            for chunk in resp.iter_bytes(8192):
                fh.write(chunk)

    logger.info("Extracting categories…")
    categories: list[dict] = []
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith(".json"):
                f = tar.extractfile(member)
                if f:
                    data = json.load(f)
                    categories = data.get("categories", [])
                    break
    tar_path.unlink(missing_ok=True)
    cats_path.write_text(json.dumps(categories))
    logger.info("Saved %d iNat2021 categories to cache", len(categories))
    return categories


def _build_label_map(model) -> dict[int, tuple[str, str]]:
    """Return {class_idx: (scientific_name, common_name)}."""
    # timm may bundle label names in the pretrained config for HuggingFace-hosted models
    label_names = getattr(getattr(model, "pretrained_cfg", None), "label_names", None)
    if label_names and len(label_names) == NUM_CLASSES:
        logger.info("Using %d label names from pretrained_cfg", len(label_names))
        return {i: (n, n) for i, n in enumerate(label_names)}

    categories = _download_inat21_categories()
    cats_sorted = sorted(categories, key=lambda c: c["id"])
    return {
        i: (c["name"], c.get("common_name") or c["name"])
        for i, c in enumerate(cats_sorted)
    }


def _load_model():
    global _model, _transform, _idx_to_species, _device
    if _model is not None:
        return _model

    _device = _get_device()
    logger.info("Device: %s", _device)

    logger.info("Loading model: %s (first run downloads ~1.3 GB)", MODEL_REPO)
    model = timm.create_model(MODEL_REPO, pretrained=True, num_classes=NUM_CLASSES)
    model.eval()
    model = model.to(_device)

    _idx_to_species = _build_label_map(model)

    data_cfg = timm.data.resolve_model_data_config(model)
    _transform = timm.data.create_transform(**data_cfg, is_training=False)

    _model = model
    logger.info("Model ready | %d classes | device=%s", NUM_CLASSES, _device)
    return _model


def predict(image_bytes: bytes, top_k: int = 3) -> list[Prediction]:
    model = _load_model()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(image).unsqueeze(0).to(_device)  # type: ignore[misc]

    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)[0]

    top_probs, top_idxs = probs.topk(top_k)
    logger.debug("Raw top-%d predictions:", top_k)
    results = []
    for prob, idx in zip(top_probs.tolist(), top_idxs.tolist()):
        scientific, common = _idx_to_species.get(idx, (str(idx), str(idx)))
        logger.debug("  idx=%-5d  score=%.4f  name=%s", idx, prob, scientific)
        results.append(Prediction(
            species=scientific,
            common_name=common,
            confidence=round(prob, 4),
        ))
    return results
