#!/usr/bin/env python3
"""Build the smith.wiki registry: one entry per public research repository.

A research repository is a public repository of the organization tagged with the
TOPIC topic. GitHub Pages serves each one at https://smith.wiki/<repo>/ because
the organization site owns the custom domain.
"""

from __future__ import annotations

import html
import json
import os
import shutil
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ORG = "smith-wiki"
TOPIC = "smith-wiki-research"
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"


def research_repositories() -> list[dict]:
    request = Request(
        f"https://api.github.com/orgs/{ORG}/repos?type=public&per_page=100",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=30) as response:
        repos = json.load(response)
    found = [repo for repo in repos if TOPIC in repo.get("topics", []) and not repo["archived"]]
    return sorted(found, key=lambda repo: repo["created_at"], reverse=True)


def entry(repo: dict) -> str:
    name = html.escape(repo["name"])
    description = html.escape(repo.get("description") or "")
    return (
        f'<li><a href="/{name}/">{name}</a>'
        f'{" &mdash; " + description if description else ""}'
        f' <a class="source" href="{html.escape(repo["html_url"])}">source</a></li>'
    )


def main() -> int:
    repos = research_repositories()
    if not repos:
        print(f"no public repository carries the {TOPIC} topic", file=sys.stderr)
        return 1
    template = (ROOT / "index.template.html").read_text(encoding="utf-8")
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    items = "\n".join(entry(repo) for repo in repos)
    (OUT / "index.html").write_text(template.replace("{{ research }}", items), encoding="utf-8")
    shutil.copy(ROOT / "404.html", OUT / "404.html")
    (OUT / ".nojekyll").touch()
    print(f"registry lists {len(repos)} research repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
