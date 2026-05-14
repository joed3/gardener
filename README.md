# Gardener

A self-hosted plant identification app. Snap or upload a photo, get species predictions from a local ML model, read the Wikipedia article for the top match, and log finds to a personal garden collection with timestamp and GPS coordinates.

No subscription. No account. All inference runs locally. The only external calls are fetching a Wikipedia summary and the one-time download of the model weights (~1.3 GB) from HuggingFace on first startup.

---

## Contents

- [Requirements](#requirements)
- [Quick start — local](#quick-start--local)
- [Quick start — Docker](#quick-start--docker)
- [Using the app on desktop](#using-the-app-on-desktop)
- [Using the app on mobile (PWA)](#using-the-app-on-mobile-pwa)
- [Development](#development)
- [Project structure](#project-structure)
- [Versioning](#versioning)

---

## Requirements

| Tool | Minimum version | Notes |
|---|---|---|
| Python | 3.11 | Backend runtime |
| Node.js | 20 | Frontend build |
| npm | 10 | Comes with Node 20 |
| Docker + Compose | any recent | Only needed for the Docker path |

The first backend startup downloads the plant classifier model (~330 MB) from HuggingFace into `~/.cache/huggingface`. Subsequent starts use the cached copy.

---

## Quick start — local

Running the backend outside Docker is the recommended path on Apple Silicon because the Metal GPU (MPS) is available natively but cannot be accessed from inside a Docker Linux VM.

```bash
git clone <repo-url> gardener && cd gardener
```

**Terminal 1 — backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
```

Install PyTorch **before** the rest of the requirements. The install command differs by platform:

| Platform | Command |
|---|---|
| macOS Apple Silicon | `pip install torch torchvision` |
| macOS Intel | `pip install torch torchvision` |
| Linux CPU-only | `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu` |
| Linux + CUDA | `pip install torch torchvision` (picks up CUDA automatically) |

Then install the remaining dependencies and start the server:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

**First run** downloads the model weights (~1.3 GB) from HuggingFace and the iNat2021 species list (~10 MB). Both are cached in `~/.cache/` and reused on every subsequent startup. Expect the first request to take a minute or two while the model loads.

To confirm MPS is active, look for this line in the backend log:

```
INFO  classifier:classifier.py  Device: mps
```

If you see `cpu` instead, torch was installed without MPS support — reinstall from the table above.

**Terminal 2 — frontend**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

> **Docker vs. local**: Docker is convenient but runs inference on CPU (the Linux VM cannot access the Mac GPU). For the best experience on Apple Silicon, run the backend locally and Docker-compose only the frontend, or run everything locally as shown above.

---

## Quick start — Docker

```bash
docker compose up
```

This builds both images and starts the backend on port 8001 and the frontend on port 3000. The HuggingFace model cache is persisted in a Docker volume so it survives container restarts.

### Rebuilding containers

Rebuild after changing Python dependencies, Dockerfiles, or environment variables:

```bash
# Rebuild all images and restart
docker compose up --build

# Rebuild a single service (faster when only the backend changed)
docker compose up --build backend

# Force a full rebuild from scratch (clears layer cache)
docker compose build --no-cache
docker compose up
```

### Stopping and cleaning up

```bash
# Stop containers, keep volumes (model cache preserved)
docker compose down

# Stop containers and delete volumes (removes downloaded model cache)
docker compose down -v
```

### Switching the ML model

The classifier uses [EVA-02 Large fine-tuned on iNaturalist 2021](https://huggingface.co/timm/eva02_large_patch14_clip_336.merged2b_ft_inat21), downloaded automatically from HuggingFace on first startup (~1.3 GB). It recognises **10,000 species** including common garden plants, crops, and wildflowers.

The model is controlled by the `PLANT_MODEL_REPO` env var and can point to any [timm](https://huggingface.co/timm) model hosted on HuggingFace:

| Model | Size | top-1 (iNat21) | Notes |
|---|---|---|---|
| `hf_hub:timm/eva02_large_patch14_clip_336.merged2b_ft_inat21` | 1.3 GB | 92% | Default |
| `hf_hub:timm/vit_large_patch14_clip_336.openai_ft_inat21` | 1.2 GB | ~88% | Faster |

To switch models, update `PLANT_MODEL_REPO` in `docker-compose.yml` and clear the cached weights:

```bash
docker compose down -v && docker compose up --build
```

The `-v` flag clears the HuggingFace model cache so the new weights are downloaded fresh.

---

## Using the app on desktop

1. **Identify a plant** — navigate to the home page, click **Upload Photo**, and choose an image file. Click **Identify Plant**. The top three species predictions appear with confidence bars.
2. **Read the Wikipedia panel** — the top prediction's Wikipedia summary (thumbnail, one-sentence description, first paragraph) loads automatically below the results. Click **Full Wikipedia article →** to open the full page.
3. **Save to your garden** — optionally add a note, then click **Save to My Garden**. Your browser's geolocation (city-level on desktop) is attached if you granted permission.
4. **Browse your collection** — click **My Garden** in the header to see all saved plants. Click any card to expand it with full details and a map pin when coordinates are available.

---

## Using the app on mobile (PWA)

Gardener is a Progressive Web App. Once installed it works like a native app: full-screen, offline shell, and direct camera access.

### Install on Android (Chrome)

1. Open [http://localhost:3000](http://localhost:3000) in Chrome.
2. Tap the **⋮** menu → **Add to Home screen**.
3. Confirm the name and tap **Add**. The Gardener icon appears on your home screen.

### Install on iOS (Safari)

1. Open [http://localhost:3000](http://localhost:3000) in Safari.
   - Safari is required; Chrome on iOS cannot install PWAs.
2. Tap the **Share** button (box with an upward arrow) at the bottom of the screen.
3. Scroll down and tap **Add to Home Screen**.
4. Confirm the name and tap **Add**.

### Using the camera on mobile

- The home page shows a **Use Camera** button that activates the rear camera via `getUserMedia`.
- If camera permission is denied the **Upload Photo** fallback lets you pick from your photo library.
- Photos taken natively on your phone embed GPS coordinates in EXIF data. Gardener reads these and uses them instead of (less-accurate) browser geolocation when they are present.

### Accessing from other devices on the same network

If your backend and frontend are running on a desktop machine, replace `localhost` with that machine's local IP address (e.g. `192.168.1.42`) and update the frontend's API URL:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://192.168.1.42:8001
```

Then restart the frontend dev server. You can then open the app on your phone by navigating to `http://192.168.1.42:3000`.

---

## Development

### Running tests

```bash
# Backend (from backend/)
source .venv/bin/activate
pytest                     # run all tests
pytest -v --tb=short       # verbose output

# Frontend (from frontend/)
npm test                   # run Jest tests
npm test -- --watch        # watch mode during development
```

### Linting and formatting

```bash
# Backend
ruff check .               # lint
ruff format .              # format in-place
ruff check --fix .         # lint with auto-fix

# Frontend
npm run lint               # ESLint
npm run type-check         # TypeScript strict check
```

### Pre-commit hooks

Install the hooks once after cloning:

```bash
pip install pre-commit
pre-commit install
```

On every `git commit` the hooks automatically run:
- Trailing whitespace removal and end-of-file fixes
- YAML validity check
- `ruff check --fix` + `ruff format` on Python files
- `next lint` (ESLint) on TypeScript/TSX files

Run all hooks manually without committing:

```bash
pre-commit run --all-files
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./garden.db` | SQLAlchemy database URL |
| `PLANT_MODEL_REPO` | `hf_hub:timm/eva02_large_patch14_clip_336.merged2b_ft_inat21` | HuggingFace timm model to use |
| `INAT_CACHE_DIR` | `/root/.cache/inat21` | Where the iNat2021 categories file is cached |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8001` | Backend URL used by the browser |

### Adding a new backend endpoint

1. Add a route function in `backend/main.py`.
2. Add a Pydantic schema in `backend/models.py` if the endpoint has a new request or response shape.
3. Write a test in `backend/tests/test_main.py` using the `client` fixture.
4. Run `pytest` and `ruff check .` before committing.

### CI

GitHub Actions runs two jobs on every push and pull request to `main`:

| Job | Steps |
|---|---|
| `backend` | `pip install -r requirements-dev.txt` → `ruff check` → `ruff format --check` → `pytest` |
| `frontend` | `npm ci` → `next lint` → `tsc --noEmit` → `jest --ci` |

Both jobs must pass before a pull request can be merged.

---

## Project structure

```
gardener/
├── VERSION                    # canonical version (source of truth)
├── CHANGELOG.md               # human-readable release history
├── .pre-commit-config.yaml    # pre-commit hook definitions
├── docker-compose.yml
│
├── scripts/
│   └── bump-version.sh        # semantic version bump + git tag
│
├── backend/                   # FastAPI application
│   ├── main.py                # routes and app lifecycle
│   ├── classifier.py          # HuggingFace inference wrapper
│   ├── wiki.py                # Wikipedia REST client
│   ├── database.py            # SQLAlchemy models and session
│   ├── models.py              # Pydantic request/response schemas
│   ├── pyproject.toml         # project metadata, ruff config, pytest config
│   ├── requirements.txt       # runtime dependencies
│   ├── requirements-dev.txt   # runtime + test/lint dependencies
│   ├── uploads/               # saved plant images (git-ignored)
│   └── tests/
│       ├── test_main.py       # API endpoint tests
│       ├── test_classifier.py # label parsing and predict() tests
│       └── test_wiki.py       # Wikipedia client tests
│
├── frontend/                  # Next.js PWA
│   ├── app/
│   │   ├── layout.tsx         # root layout and navigation
│   │   ├── page.tsx           # identify page
│   │   └── garden/page.tsx    # garden collection page
│   ├── components/
│   │   ├── CameraCapture.tsx  # getUserMedia + file upload
│   │   ├── PlantCard.tsx      # single prediction with confidence bar
│   │   ├── WikiPanel.tsx      # Wikipedia summary display
│   │   ├── SaveButton.tsx     # upload image + save garden entry
│   │   └── GardenGrid.tsx     # collection grid + detail modal
│   ├── __tests__/             # Jest + Testing Library component tests
│   ├── public/manifest.json   # PWA manifest
│   └── next.config.mjs        # Next.js config + next-pwa
│
└── .github/
    └── workflows/ci.yml       # GitHub Actions CI definition
```

---

## Versioning

Gardener uses [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

| Change type | When to bump |
|---|---|
| `patch` | Bug fixes, dependency updates, documentation |
| `minor` | New features that are backwards-compatible |
| `major` | Breaking changes to the API or storage format |

The canonical version lives in `VERSION` at the repository root. `backend/pyproject.toml` and `frontend/package.json` are kept in sync by the bump script.

### Cutting a release

```bash
# Patch release (bug fix)
./scripts/bump-version.sh patch

# Minor release (new feature)
./scripts/bump-version.sh minor

# Major release (breaking change)
./scripts/bump-version.sh major
```

The script:
1. Validates the working tree is clean.
2. Increments the chosen component and resets lower components to zero.
3. Writes the new version to `VERSION`, `backend/pyproject.toml`, and `frontend/package.json`.
4. Creates a git commit (`chore: bump version to X.Y.Z`) and an annotated tag (`vX.Y.Z`).

Push the commit and tag together:

```bash
git push && git push --tags
```

### Changelog

Update `CHANGELOG.md` before running the bump script. Move items from `[Unreleased]` to a new dated section:

```markdown
## [0.2.0] — 2026-06-01

### Added
- ...

### Fixed
- ...
```

Accepted section headers: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
