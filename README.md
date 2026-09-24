# smith.wiki

The organization site of Smith Wiki. It owns the `smith.wiki` custom domain, so
GitHub Pages serves every public repository of the organization at
`smith.wiki/<repository>/`.

- `build.py` lists the public repositories tagged `smith-wiki-research` and
  writes the registry page from `index.template.html`.
- `404.html` redirects old root URLs of the first wiki to `/wiki/`.
- `.github/workflows/deploy.yml` rebuilds the registry on push, hourly, on a
  `research-published` repository dispatch, and on demand.

A research repository appears in the registry once it is public, has GitHub
Pages enabled, and carries the `smith-wiki-research` topic.
