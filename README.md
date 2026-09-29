# smith.wiki

The organization site of Smith Wiki. It owns the `smith.wiki` custom domain, so
GitHub Pages serves every public repository of the organization at
`smith.wiki/<repository>/`.

`site/` is published as is:

- `index.html` is the product page: what Smith Wiki is, the live example
  (`andy.smith.wiki`, served from `smith-wiki/cards`), and how to ask for a
  wiki (X `@andysmithai`, `inbox@andysmith.ai`);
- `404.html` redirects old root URLs of the first wiki to `/wiki/`;
- `assets/` holds the design tokens, fonts, styles, and analytics.

`.github/workflows/deploy.yml` deploys `site/` on push to `main` and on demand.
