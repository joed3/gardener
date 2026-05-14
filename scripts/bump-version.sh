#!/usr/bin/env bash
# bump-version.sh <major|minor|patch>
#
# Updates the canonical VERSION file, backend/pyproject.toml,
# frontend/package.json, and creates an annotated git tag.
#
# Usage:
#   ./scripts/bump-version.sh patch   # 0.1.0 → 0.1.1
#   ./scripts/bump-version.sh minor   # 0.1.0 → 0.2.0
#   ./scripts/bump-version.sh major   # 0.1.0 → 1.0.0

set -euo pipefail

PART="${1:-}"
if [[ -z "$PART" ]]; then
  echo "Usage: $0 <major|minor|patch>" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION_FILE="$ROOT/VERSION"
BACKEND_TOML="$ROOT/backend/pyproject.toml"
FRONTEND_PKG="$ROOT/frontend/package.json"

current=$(cat "$VERSION_FILE" | tr -d '[:space:]')

IFS='.' read -r major minor patch <<< "$current"

case "$PART" in
  major) major=$((major + 1)); minor=0; patch=0 ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  patch) patch=$((patch + 1)) ;;
  *)
    echo "Error: part must be major, minor, or patch (got '$PART')" >&2
    exit 1
    ;;
esac

next="$major.$minor.$patch"

# Ensure working tree is clean before bumping
if ! git -C "$ROOT" diff --quiet || ! git -C "$ROOT" diff --cached --quiet; then
  echo "Error: working tree has uncommitted changes. Commit or stash them first." >&2
  exit 1
fi

echo "Bumping $current → $next"

# Update VERSION
echo "$next" > "$VERSION_FILE"

# Update backend/pyproject.toml  [project] version = "..."
sed -i.bak "s/^version = \"$current\"/version = \"$next\"/" "$BACKEND_TOML" \
  && rm -f "$BACKEND_TOML.bak"

# Update frontend/package.json  "version": "..."
# Use python3 for portable JSON rewrite (avoids jq dependency)
python3 - "$FRONTEND_PKG" "$next" <<'PYEOF'
import sys, json
path, ver = sys.argv[1], sys.argv[2]
with open(path) as f:
    pkg = json.load(f)
pkg["version"] = ver
with open(path, "w") as f:
    json.dump(pkg, f, indent=2)
    f.write("\n")
PYEOF

# Commit and tag
git -C "$ROOT" add "$VERSION_FILE" "$BACKEND_TOML" "$FRONTEND_PKG"
git -C "$ROOT" commit -m "chore: bump version to $next"
git -C "$ROOT" tag -a "v$next" -m "Release v$next"

echo "Done. Created commit and tag v$next."
echo "Push with: git push && git push --tags"
