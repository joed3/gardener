# Changelog

All notable changes to Gardener are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-05-14

### Added
- FastAPI backend with plant identification via HuggingFace `umucahit/PlantNet-300K`
- Wikipedia REST proxy (`GET /wiki/{species}`) with species → common-name fallback
- SQLite garden log (`POST /garden`, `GET /garden`) with EXIF datetime extraction
- Image upload endpoint storing files under `backend/uploads/`
- Next.js 14 PWA frontend with camera capture and file upload
- Identify page: top-3 predictions with confidence bars, WikiPanel, Save to Garden
- Garden page: photo grid with expandable detail cards and OpenStreetMap pin
- Geolocation capture on identify page; GPS coordinates saved with each entry
- PWA manifest for Add to Home Screen on iOS and Android
- Tailwind CSS with custom `garden-*` green palette
- 17 backend unit tests (pytest) and 7 frontend component tests (Jest + RTL)
- ruff lint/format for Python; ESLint + TypeScript strict mode for frontend
- Pre-commit hooks for trailing whitespace, YAML check, ruff, and ESLint
- GitHub Actions CI: two parallel jobs (backend, frontend) on push and PR
- Docker Compose setup for one-command local deployment

[Unreleased]: https://github.com/placeholder/gardener/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/placeholder/gardener/releases/tag/v0.1.0
