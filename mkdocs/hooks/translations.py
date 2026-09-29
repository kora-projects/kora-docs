"""Marks pages that exist in the other language (used by every docs build).

The language switcher (overrides/partials/alternate.html) links to the same
page in the other language when it exists, and main.html emits hreflang
alternates only for real translations.
"""
from pathlib import Path


def on_page_markdown(markdown, page, config, files):
    other_lang = "ru" if config.theme["language"] == "en" else "en"
    other_docs = Path(config.docs_dir).parent / other_lang
    page.meta["kora_has_translation"] = (other_docs / page.file.src_uri).is_file()
    return markdown
