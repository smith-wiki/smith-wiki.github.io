# smith.wiki

The organization site of Smith Wiki. It owns the `smith.wiki` custom domain, so
GitHub Pages serves every public repository of the organization at
`smith.wiki/<repository>/`.

- `index.template.html` is the product page: what Smith Wiki is, the live
  example (`andy.smith.wiki`, served from `smith-wiki/cards`), and how to ask
  for a wiki (X `@andysmithai`, `inbox@andysmith.ai`). It ends with the
  registry of earlier research wikis.
- `build.py` lists the public repositories tagged `smith-wiki-research` into
  that registry and writes `_site/` with `assets/` (design tokens, fonts,
  styles, analytics).
- `404.html` redirects old root URLs of the first wiki to `/wiki/`.
- `.github/workflows/deploy.yml` rebuilds the site on push, hourly, on a
  `research-published` repository dispatch, and on demand.

A research repository appears in the registry once it is public, has GitHub
Pages enabled, and carries the `smith-wiki-research` topic.
