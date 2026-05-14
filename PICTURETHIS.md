# PlantID — Free, Local PictureThis Alternative

A self-hosted plant identification web app. Snap or upload a photo, get species predictions from a local ML model, view the Wikipedia article for the top match, and log finds to a personal garden collection with time and GPS location. No subscription, no data leaving your machine (Wikipedia lookups are the only external call).

---

## Architecture

```
Browser (Next.js PWA)
  │
  ├─ POST /api/identify    →  FastAPI  →  HuggingFace plant classifier (local)
  ├─ GET  /api/wiki/{name} →  FastAPI  →  Wikipedia REST API (external)
  ├─ POST /api/garden      →  FastAPI  →  SQLite
  └─ GET  /api/garden      →  FastAPI  →  SQLite
```

Two processes, both running locally:
- **Frontend**: Next.js dev server (or `next build` static export)
- **Backend**: Python FastAPI serving the ML model and SQLite database

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 14 (App Router) + Tailwind | PWA support, easy camera API access |
| Backend | Python FastAPI + Uvicorn | Async, easy HuggingFace integration |
| ML inference | `transformers` + `torch` | Standard HuggingFace pipeline |
| Database | SQLite via SQLAlchemy | Zero-config, single file, local |
| Plant info | Wikipedia REST API | Free, no key, rich content, reliable |
| Location | Browser Geolocation API + EXIF fallback | Works on mobile and desktop |
| Model | See Model Selection below | |

---

## Model Selection

### Recommended: Pl@ntNet-300K classifier
A ViT or EfficientNet fine-tuned on the PlantNet-300K dataset (~306k images, ~1k species).

Candidates to evaluate on HuggingFace Hub:
- `umucahit/PlantNet-300K` — ViT-B/16, ~330 MB
- `google/efficientnet-b4` fine-tuned variants on iNaturalist
- Any `image-classification` pipeline model tagged `plants` on HuggingFace

Benchmark a few with your own test photos and pick the one with best accuracy for your region/use case.

### Alternative: Ollama vision model (zero-shot)
If you have Ollama installed, `llama3.2-vision` or `llava` can identify plants via a structured prompt. Less accurate than a specialized classifier but requires no Python ML dependencies — just `ollama serve`.

**Start with the HuggingFace classifier; fall back to Ollama if setup proves painful.**

---

## Project Structure

```
plantid/
├── frontend/               # Next.js app
│   ├── app/
│   │   ├── page.tsx        # Camera / upload UI
│   │   ├── result/[id]/    # Identification result
│   │   └── garden/         # Saved plant collection
│   ├── components/
│   │   ├── CameraCapture.tsx
│   │   ├── PlantCard.tsx
│   │   ├── WikiPanel.tsx
│   │   └── GardenGrid.tsx
│   ├── public/manifest.json  # PWA manifest
│   └── next.config.ts
│
├── backend/                # FastAPI app
│   ├── main.py             # App entrypoint, routes
│   ├── classifier.py       # Model loading + inference
│   ├── wiki.py             # Wikipedia REST API client
│   ├── database.py         # SQLAlchemy models + session
│   ├── models.py           # Pydantic schemas
│   ├── garden.db           # SQLite file (git-ignored)
│   └── requirements.txt
│
└── docker-compose.yml      # Optional: run both together
```

---

## Backend API

### `POST /identify`
```json
// Request: multipart/form-data
{ "image": <file> }

// Response
{
  "predictions": [
    { "species": "Monstera deliciosa", "common_name": "Swiss Cheese Plant", "confidence": 0.91 },
    { "species": "Monstera adansonii", "common_name": "Monkey Mask", "confidence": 0.06 },
    { "species": "Rhaphidophora tetrasperma", "common_name": "Mini Monstera", "confidence": 0.02 }
  ]
}
```

### `GET /wiki/{species_name}`
Proxied through the backend so the frontend has a single origin to talk to. Uses the [Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/) — no key needed.

```
GET /wiki/Monstera%20deliciosa
→ fetches https://en.wikipedia.org/api/rest_v1/page/summary/{species_name}
```

```json
// Response (subset of Wikipedia summary object, passed through as-is)
{
  "title": "Monstera deliciosa",
  "description": "Species of flowering plant in the family Araceae",
  "extract": "Monstera deliciosa, the Swiss cheese plant...",
  "thumbnail": { "source": "https://upload.wikimedia.org/...", "width": 320, "height": 427 },
  "content_urls": { "desktop": { "page": "https://en.wikipedia.org/wiki/Monstera_deliciosa" } }
}
```

If the species name has no Wikipedia article, fall back to searching by common name, then return `null` gracefully.

### `POST /garden`
```json
// Request
{
  "species": "Monstera deliciosa",
  "common_name": "Swiss Cheese Plant",
  "confidence": 0.91,
  "image_path": "...",        // stored locally under backend/uploads/
  "notes": "Found in garden, NW corner",
  "captured_at": "2026-05-14T15:32:00Z",   // ISO 8601; from EXIF if available, else client time
  "latitude": 37.7749,                      // null if user denies geolocation
  "longitude": -122.4194
}

// Response: { "id": 42 }
```

### `GET /garden`
Returns all saved entries, sorted by `captured_at` descending.

```json
[
  {
    "id": 42,
    "species": "Monstera deliciosa",
    "common_name": "Swiss Cheese Plant",
    "confidence": 0.91,
    "image_url": "/uploads/abc123.jpg",
    "notes": "Found in garden, NW corner",
    "captured_at": "2026-05-14T15:32:00Z",
    "latitude": 37.7749,
    "longitude": -122.4194
  }
]
```

---

## Frontend Pages

### `/` — Identify
1. Camera capture button (uses `getUserMedia`) or file upload fallback
2. Request geolocation permission in the background as soon as the page loads — store coords for when the user saves
3. Preview the image, hit **Identify**
4. POST to `/api/identify`, show top-3 results with confidence bars
5. **Top result panel** — immediately fetches Wikipedia summary (`GET /api/wiki/{species}`) and renders:
   - Thumbnail image
   - One-sentence description
   - First paragraph of the extract (collapsible)
   - "Full Wikipedia article →" link
6. **Save to garden** button attaches current timestamp + geolocation coords (or null if denied)

### `/garden` — My Collection
- Grid of saved plants (photo thumbnail + species name + date)
- Tap to expand: full photo, species + confidence, Wikipedia snippet, notes, captured timestamp, map pin (if coords exist — use a static map tile from OpenStreetMap, no key required)

---

## Implementation Plan

### Phase 1 — Backend core (≈1 day)
- [ ] `classifier.py`: load model once at startup, expose `predict(image_bytes) → list[Prediction]`
- [ ] `POST /identify` endpoint
- [ ] `wiki.py`: async `httpx` client wrapping the Wikipedia REST summary endpoint, with species-name → common-name fallback
- [ ] `GET /wiki/{species_name}` endpoint
- [ ] Basic FastAPI app with CORS for localhost frontend

### Phase 2 — Frontend identify flow (≈1 day)
- [ ] Camera capture component (mobile-first, graceful desktop fallback)
- [ ] Request geolocation on page load; store coords in component state
- [ ] Call backend, render top-3 predictions with confidence bars
- [ ] `WikiPanel` component: fetch and render Wikipedia summary for top prediction (thumbnail, extract, link)
- [ ] Basic styling with Tailwind

### Phase 3 — Garden / history (≈0.5 day)
- [ ] SQLite schema: add `captured_at`, `latitude`, `longitude` columns
- [ ] `POST /garden`, `GET /garden` endpoints
- [ ] On save: read EXIF `DateTimeOriginal` from uploaded image (use `Pillow`) for `captured_at`; fall back to request time
- [ ] Garden page: grid view + expanded detail card with OSM static map tile when coords present

### Phase 4 — Polish (≈0.5 day)
- [ ] PWA manifest + service worker (use `next-pwa`)
- [ ] Images stored under `backend/uploads/`, served as static files
- [ ] `docker-compose.yml` to start both services with one command

---

## Setup (target developer experience)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# First run downloads model (~330 MB, cached under ~/.cache/huggingface)
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev   # http://localhost:3000
```

Or with Docker:
```bash
docker compose up
```

---

## Key Dependencies

### Backend `requirements.txt`
```
fastapi
uvicorn[standard]
python-multipart
transformers
torch
Pillow          # image preprocessing + EXIF extraction
sqlalchemy
httpx           # async Wikipedia API calls
```

### Frontend `package.json` (additions)
```
next
react / react-dom
tailwindcss
next-pwa
```

---

## Notes & Trade-offs

- **Accuracy**: A specialized 1k-species classifier will miss rare species. For common houseplants and garden plants it should perform well. The PlantNet API (free tier, 500 req/day) is available as a drop-in accuracy upgrade later without changing the frontend at all — just swap `classifier.py`.
- **Inference speed**: On CPU, a ViT-B/16 takes ~0.5–2s per image. Acceptable for personal use. On Apple Silicon with MPS backend (`device="mps"`), it's near-instant.
- **Species metadata**: The model outputs a species label. For a common name lookup, use the GBIF API (free, no key required) or bundle a small CSV from the PlantNet-300K label map.
- **Wikipedia coverage**: Most species with a binomial name have a Wikipedia article. The REST summary endpoint (`/page/summary/{title}`) returns a clean extract and thumbnail — no scraping, no API key. If the species page is missing, the backend tries the common name before returning null; the `WikiPanel` component handles null gracefully with a "No Wikipedia article found" state.
- **Location accuracy**: Browser `navigator.geolocation` is accurate to ~10m on mobile with GPS. On desktop it falls back to IP geolocation (city-level). EXIF coordinates from photos taken on another device (e.g., uploaded from camera roll) are extracted by Pillow and used instead when present — these are typically more accurate.
- **Map display**: OpenStreetMap static tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`) need no API key. For a single pin marker, render a small `<img>` pointing at `https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lon}&zoom=15&markers={lat},{lon}` — no JavaScript map library required for a read-only pin view.
- **Privacy**: The only external call is the Wikipedia summary lookup (species name sent to Wikipedia). Images and location data stay on your machine.
- **Timezone**: Store `captured_at` as UTC in SQLite; display in local timezone in the frontend using `Intl.DateTimeFormat`.
