#!/usr/bin/env python3
"""Verify public-safe dashboard links and obvious sensitive text leaks."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [ROOT / "index.html", *sorted((ROOT / "dashboards").glob("*.html"))]
FORBIDDEN = [
    "/Users/",
    "77040",
    "github-pat",
    "credential",
    "secret",
    "NextDecade Enterprise Skill Source",
    "Active Directory R3",
    "out/dashboard.html",
]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs = dict(attrs)
        href = attrs.get("href")
        if href:
            self.hrefs.append(href)


def assert_no_forbidden_text(path):
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    for needle in FORBIDDEN:
        if needle.lower() in lowered:
            raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden public text: {needle}")


def check_local_link(source, href):
    if href.startswith("#"):
        return
    parsed = urlparse(href)
    if parsed.scheme in {"http", "https", "mailto"}:
        return
    target = (source.parent / href).resolve()
    if not str(target).startswith(str(ROOT.resolve())):
        raise AssertionError(f"{source.relative_to(ROOT)} links outside repo: {href}")
    if not target.exists():
        raise AssertionError(f"{source.relative_to(ROOT)} broken local link: {href}")


def check_live_url(url):
    req = Request(url, headers={"User-Agent": "codex-public-dashboard-link-check/1.0"})
    with urlopen(req, timeout=20) as response:
        if response.status >= 400:
            raise AssertionError(f"{url} returned HTTP {response.status}")


def main():
    live_urls = set()
    for path in HTML_FILES:
        assert_no_forbidden_text(path)
        parser = LinkParser()
        parser.feed(path.read_text(encoding="utf-8"))
        for href in parser.hrefs:
            check_local_link(path, href)
            if href.startswith(("http://", "https://")):
                live_urls.add(href)
    for url in sorted(live_urls):
        check_live_url(url)
    print(f"verified {len(HTML_FILES)} html files and {len(live_urls)} live urls")


if __name__ == "__main__":
    main()
