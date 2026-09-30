"""Post-build step for the published site (run by the Pages workflow).

The site is published at kora-projects.github.io/kora-docs/. Addresses from
before the v1/v2 split are still indexed and linked, so this script writes a
redirect stub for each of them:

  /kora-docs/<lang>/<path>/  -> /kora-docs/v1/<lang>/<path>/ (pre-split docs, same content)

A zero-delay meta refresh plus a canonical link is what search engines treat
as a permanent redirect on static hosting. The refresh target is a root path,
so the stubs also work when the site is served locally under /kora-docs/.

It also drops blog URLs from the v1 sitemaps: v1 blog pages declare their v2
copy as canonical, and a sitemap should list canonical URLs only.

Usage: python mkdocs/hooks/legacy_redirects.py public
"""
import re
import sys
from pathlib import Path

SITE = "https://kora-projects.github.io/kora-docs/"
PREFIX = "/kora-docs/"

STUB = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={path}">
<script>location.replace("{path}" + location.hash);</script>
</head>
<body><a href="{path}">{title}</a></body>
</html>
"""


def _title(page):
    match = re.search(r"<title>(.*?)</title>", page.read_text(encoding="utf-8"), re.S)
    return match.group(1).strip() if match else "Kora Framework"


def _stub(public, rel, target, lang, title):
    path = public / rel / "index.html"
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(STUB.format(lang=lang, url=SITE + target, path=PREFIX + target, title=title), encoding="utf-8")


def main(public):
    public = Path(public)

    # Pre-split /kora-docs/<lang>/<path>/ -> /kora-docs/v1/<lang>/<path>/.
    for lang in ("ru", "en"):
        v1 = public / "v1" / lang
        for page in v1.rglob("index.html"):
            rel = page.parent.relative_to(v1).as_posix()
            if rel == "." or rel.startswith(("blog", "assets", "search")):
                continue
            _stub(public, f"{lang}/{rel}", f"v1/{lang}/{rel}/", lang, _title(page))

        sitemap = v1 / "sitemap.xml"
        if sitemap.exists():
            xml = re.sub(r"\s*<url>\s*<loc>[^<]*/blog/[^<]*</loc>.*?</url>", "", sitemap.read_text(encoding="utf-8"), flags=re.S)
            sitemap.write_text(xml, encoding="utf-8")
            (v1 / "sitemap.xml.gz").unlink(missing_ok=True)


if __name__ == "__main__":
    main(sys.argv[1])
