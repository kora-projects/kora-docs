#!/usr/bin/env bash
#
# Serve the docs locally the same way GitHub Pages does (https://koraframework.io/),
# so the site root redirects into the correct landing page just like production.
#
# CI (.github/workflows/publish-pages.yml) assembles a `public/` tree where the
# root redirect (mkdocs/index.html), the shortcuts from mkdocs/redirects and the
# legacy /kora-docs/... redirect stubs live next to the versioned builds.
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
OUT=".local-serve"

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

# Assemble the same layout CI ships, served from the site root.
rm -rf "$OUT"
mkdir -p "$OUT"
cp -r mkdocs/generated/v1 "$OUT/v1"
cp -r mkdocs/generated/v2 "$OUT/v2"
cp mkdocs/index.html "$OUT/index.html"   # root redirect
cp -r mkdocs/redirects/. "$OUT"          # CNAME, robots.txt, sitemap index, llms.txt, 404, shortcuts
"$PYTHON" mkdocs/hooks/legacy_redirects.py "$OUT"   # old /kora-docs/... URLs

echo "Serving http://127.0.0.1:${PORT}/"
cd "$OUT"
exec "$PYTHON" -m http.server "$PORT" --bind 127.0.0.1
