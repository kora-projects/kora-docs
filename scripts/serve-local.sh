#!/usr/bin/env bash
#
# Serve the docs locally the same way GitHub Pages does (https://kora-projects.github.io/kora-docs/),
# so /kora-docs/ serves the landing page just like production.
#
# CI (.github/workflows/publish-pages.yml) assembles a `public/` tree where the
# v2 landings are moved to /kora-docs/ and /kora-docs/ru/, and the shortcuts from
# mkdocs/redirects (incl. /v2/<lang>/ -> landing) and the legacy redirect stubs
# live next to the versioned builds.
# `mkdocs build` alone only produces mkdocs/generated/v1 and mkdocs/generated/v2,
# so this script reproduces the CI assembly.
#
# Usage:
#   ./scripts/serve-local.sh                # rebuilds (if mkdocs is available), then serves
#   SKIP_BUILD=1 ./scripts/serve-local.sh   # reuse existing mkdocs/generated
#   PORT=9000 ./scripts/serve-local.sh
#
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"
ROOT=".local-serve"
OUT="$ROOT/kora-docs"   # GitHub Pages publishes the project site under /kora-docs/

# Debian/Ubuntu (incl. WSL) ship only `python3`; `python` exists only with python-is-python3.
PYTHON="$(command -v python3 || command -v python || true)"
if [[ -z "$PYTHON" ]]; then
  echo "Python 3 not found - install it (e.g. sudo apt install python3)." >&2
  exit 1
fi

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  if command -v mkdocs >/dev/null 2>&1; then
    MKDOCS=(mkdocs)
  elif "$PYTHON" -c "import mkdocs" >/dev/null 2>&1; then
    MKDOCS=("$PYTHON" -m mkdocs)
  else
    echo "mkdocs not found - install it: $PYTHON -m pip install 'mkdocs-material==9.5.*' mkdocs-glightbox" >&2
    echo "(or run with SKIP_BUILD=1 to serve an existing mkdocs/generated)" >&2
    exit 1
  fi
  "${MKDOCS[@]}" build -f mkdocs/config/v1/ru/mkdocs.yml
  "${MKDOCS[@]}" build -f mkdocs/config/v1/en/mkdocs.yml
  "${MKDOCS[@]}" build -f mkdocs/config/v2/ru/mkdocs.yml
  "${MKDOCS[@]}" build -f mkdocs/config/v2/en/mkdocs.yml
fi

if [[ ! -d mkdocs/generated/v2 ]]; then
  echo "mkdocs/generated is empty - run a build first (install mkdocs, or unset SKIP_BUILD)." >&2
  exit 1
fi

# Assemble the same layout CI ships, served under /kora-docs/.
rm -rf "$ROOT"
mkdir -p "$OUT"
cp -r mkdocs/generated/v1 "$OUT/v1"
cp -r mkdocs/generated/v2 "$OUT/v2"
mkdir -p "$OUT/ru"
mv "$OUT/v2/en/index.html" "$OUT/index.html"      # landing at /kora-docs/
mv "$OUT/v2/ru/index.html" "$OUT/ru/index.html"   # Russian landing at /kora-docs/ru/
cp -r mkdocs/redirects/. "$OUT"          # CNAME, robots.txt, sitemap index, llms.txt, 404, /v2/<lang>/ -> landing, shortcuts
"$PYTHON" mkdocs/hooks/legacy_redirects.py "$OUT"   # pre-split /kora-docs/<lang>/... URLs

echo "Serving http://127.0.0.1:${PORT}/kora-docs/"
cd "$ROOT"
exec "$PYTHON" -m http.server "$PORT" --bind 127.0.0.1
