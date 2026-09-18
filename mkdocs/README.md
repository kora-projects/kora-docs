# Build

```shell
mkdocs build --strict --verbose -f mkdocs/config/v1/ru/mkdocs.yml
mkdocs build --strict --verbose -f mkdocs/config/v1/en/mkdocs.yml
mkdocs build --strict --verbose -f mkdocs/config/v2/ru/mkdocs.yml
mkdocs build --strict --verbose -f mkdocs/config/v2/en/mkdocs.yml
```

# Serve

```shell
mkdocs serve -f mkdocs/config/v2/ru/mkdocs.yml
```

## Blog

Blog articles are version-independent. Keep the canonical content in:

- `mkdocs/blog/en/`
- `mkdocs/blog/ru/`

Each versioned `docs/<version>/<language>/blog/` file is only a thin
`pymdownx.snippets` wrapper. This gives every build its normal versioned URL
without duplicating article content. When adding an article, create one source
per language, add a wrapper in every version, and add the page to each
`mkdocs.yml` navigation tree.
