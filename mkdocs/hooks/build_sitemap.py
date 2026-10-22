"""Merge MkDocs sitemaps into the published root URL set after site assembly."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SITE = "https://kora-projects.github.io/kora-docs/"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)
ET.register_namespace("xhtml", "http://www.w3.org/1999/xhtml")


def main(public):
    public = Path(public)
    sources = [public / "sitemap-landing.xml"]
    sources.extend(public / version / lang / "sitemap.xml"
                   for version in ("v1", "v2") for lang in ("en", "ru"))
    entries = {}
    for source in sources:
        root = ET.parse(source).getroot()
        if root.tag != f"{{{NS}}}urlset":
            raise ValueError(f"Expected urlset in {source}")
        for entry in root:
            loc = entry.findtext(f"{{{NS}}}loc")
            if not loc or not loc.startswith(SITE):
                raise ValueError(f"Invalid site URL in {source}: {loc!r}")
            relative = loc[len(SITE):]
            # Version homes canonicalize to the two landings; v1 blogs to v2.
            if relative in ("v1/en/", "v1/ru/", "v2/en/", "v2/ru/"):
                continue
            if relative.startswith(("v1/en/blog/", "v1/ru/blog/")):
                continue
            entries.setdefault(loc, entry)

    root = ET.Element(f"{{{NS}}}urlset")
    root.extend(entries[url] for url in sorted(entries))
    ET.indent(root, space="    ")
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    if len(entries) > 50000 or len(xml) > 50 * 1024 * 1024:
        raise ValueError("Combined sitemap exceeds the sitemap protocol limits")
    (public / "sitemap.xml").write_bytes(xml + b"\n")
    # Never leave a stale compressed copy after rebuilding the XML.
    (public / "sitemap.xml.gz").unlink(missing_ok=True)
    print(f"Sitemap: {len(entries)} canonical URLs")


if __name__ == "__main__":
    main(sys.argv[1])
