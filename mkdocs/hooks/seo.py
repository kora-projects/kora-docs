"""SEO / GEO hook for the v2 docs builds (en and ru).

1. Blog front matter. Blog pages under docs/v2/<lang>/blog/ are one-line
   snippet stubs (--8<-- "en/article.md") pointing into mkdocs/blog/. MkDocs
   only reads front matter from the stub itself, so the article's
   title/description/date never reached page.meta and every article was
   published without a meta description. The included article's front matter
   is copied into page.meta.

2. hreflang. Whether a page exists in the other language is recorded by
   hooks/translations.py, which every docs build (v1 and v2) registers.

3. Russian landing. landing.html translates its English markup in the browser
   from a JS dictionary. Crawlers that do not run JS (most AI crawlers) would
   index /ru/ (the v2 ru home, moved there by the Pages workflow) as English,
   so the same dictionary is applied at build time.
   The EN/RU toggle navigates to the other page, so the runtime pass finds
   nothing left to translate.

4. llms.txt. Writes an llms.txt index (title, URL, description of every page)
   next to the built site for AI assistants and answer engines.
"""
import html
import json
import re
from pathlib import Path

import yaml

MKDOCS_DIR = Path(__file__).resolve().parent.parent
BLOG_DIR = MKDOCS_DIR / "blog"
SNIPPET = re.compile(r'^\s*--8<--\s+"([^"]+)"\s*$', re.M)
FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)

_nav = None


def on_nav(nav, config, files):
    global _nav
    _nav = nav
    return nav


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri
    if not src.startswith("blog/"):
        return markdown

    include = SNIPPET.search(markdown)
    if not include:
        return markdown

    article = (BLOG_DIR / include.group(1)).read_text(encoding="utf-8")
    front_matter = FRONT_MATTER.match(article)
    if front_matter:
        for key, value in (yaml.safe_load(front_matter.group(1)) or {}).items():
            page.meta.setdefault(key, str(value).strip() if key in ("date", "updated", "description") else value)
        body = article[front_matter.end():]
    else:
        body = article

    words = len(re.findall(r"\w+", re.sub(r"```.*?```", "", body, flags=re.S)))
    page.meta["kora_blog_article"] = src != "blog/index.md"
    page.meta["kora_word_count"] = words
    page.meta["kora_reading_minutes"] = max(1, round(words / 230))
    return markdown


def _js_object(source, name):
    match = re.search(r"const " + name + r" = (\{.*?\n\s*\});", source, re.S)
    return json.loads(match.group(1)) if match else {}


def _translate_landing(output):
    ru = _js_object(output, "ru")
    attr_ru = _js_object(output, "attrRu")
    head, body_start, body = output.partition("<body")
    parts = re.split(r"(<!--.*?-->|<[^>]+>)", body, flags=re.S)
    skip = 0
    for i, part in enumerate(parts):
        if part.startswith("<"):
            tag = re.match(r"</?\s*([a-zA-Z0-9]+)", part)
            if tag and tag.group(1).lower() in ("script", "style", "code", "pre"):
                skip += -1 if part.startswith("</") else 1
            elif attr_ru and "aria-label=" in part:
                parts[i] = re.sub(
                    r'aria-label="([^"]*)"',
                    lambda m: 'aria-label="%s"' % html.escape(attr_ru.get(html.unescape(m.group(1)), html.unescape(m.group(1)))),
                    part,
                )
        elif not skip and part.strip():
            key = html.unescape(part).strip()
            if key in ru:
                leading = part[: len(part) - len(part.lstrip())]
                trailing = part[len(part.rstrip()):]
                parts[i] = leading + html.escape(ru[key], quote=False) + trailing
    return head + body_start + "".join(parts)


def on_post_page(output, page, config):
    if page.is_homepage and config.theme["language"] == "ru" and "const ru = {" in output:
        return _translate_landing(output)
    return output


def on_post_build(config):
    if _nav is None:
        return
    lang = config.theme["language"]
    blog, docs = [], []
    for page in _nav.pages:
        if page.is_homepage:
            continue
        title = page.meta.get("title") or page.title
        line = f"- [{title}]({page.canonical_url})"
        if page.meta.get("description"):
            line += ": " + " ".join(str(page.meta["description"]).split())
        if page.meta.get("keywords"):
            line += (" Темы: " if lang == "ru" else " Topics: ") + ", ".join(page.meta["keywords"]) + "."
        (blog if page.file.src_uri.startswith("blog/") else docs).append(line)

    if lang == "ru":
        header = (
            "# Kora — Java- и Kotlin-фреймворк\n\n"
            "> Kora — серверный фреймворк для Java и Kotlin: граф приложения и внедрение зависимостей строятся на этапе "
            "компиляции, генерируется прозрачный исходный код без runtime-рефлексии, код выполняется на виртуальных "
            "потоках, модули для HTTP, баз данных, Kafka, gRPC, OpenTelemetry и тестирования готовы к продакшену. "
            "Лицензия Apache 2.0, исходный код: https://github.com/kora-projects/kora\n\n"
            f"English version: {config.site_url.replace('/ru/', '/en/')}llms.txt\n"
        )
        sections = ("## Документация", "## Блог")
    else:
        header = (
            "# Kora Framework\n\n"
            "> Kora is a backend framework for Java and Kotlin that builds the application graph and dependency "
            "injection at compile time, generates transparent source code with no runtime reflection, runs "
            "application code on virtual threads, and ships production-ready modules for HTTP, databases, Kafka, "
            "gRPC, OpenTelemetry and testing. Apache 2.0 licensed, source: https://github.com/kora-projects/kora\n\n"
            f"Russian version: {config.site_url.replace('/en/', '/ru/')}llms.txt\n"
        )
        sections = ("## Documentation", "## Blog")

    text = header + "\n" + sections[0] + "\n\n" + "\n".join(docs) + "\n\n" + sections[1] + "\n\n" + "\n".join(blog) + "\n"
    Path(config.site_dir, "llms.txt").write_text(text, encoding="utf-8")
