#!/usr/bin/env python3
"""Verify public-safe dashboard links and obvious sensitive text leaks."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [ROOT / "index.html", *sorted((ROOT / "dashboards").glob("*.html"))]
PUBLIC_SITE_BASE = "https://lukestambaugh75-hue.github.io/daily-dashboards-public-safe-r0"
PUBLIC_HTML_URLS = [
    f"{PUBLIC_SITE_BASE}/index.html",
    f"{PUBLIC_SITE_BASE}/dashboards/washer.html",
    f"{PUBLIC_SITE_BASE}/dashboards/ford.html",
    f"{PUBLIC_SITE_BASE}/dashboards/baby.html",
    f"{PUBLIC_SITE_BASE}/dashboards/stroller.html",
]
SKIP_LIVE_LINK_HOSTS = {
    "facebook.com",
    "www.albeebaby.com",
    "www.bloomingdales.com",
    "www.facebook.com",
    "www.potterybarnkids.com",
}
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
REQUIRED_BY_FILE = {
    "index.html": [
        "Top 3 Quality and Price",
        "Open deep dashboard",
        "Raptor value lead",
        "Outdoor keg value",
        "PS5 and TV stack",
        "Nuna Stroller Tracker",
        "Color index",
        "Green",
        "Blue",
        "Amber",
        "Red",
        "information only",
        "not a recommendation",
    ],
    "dashboards/washer.html": [
        "Color index",
        "Green",
        "Blue",
        "Amber",
        "Red",
        "information only",
        "not a recommendation",
    ],
    "dashboards/ford.html": [
        "Color index",
        "Green",
        "Blue",
        "Amber",
        "Red",
        "information only",
        "not a recommendation",
    ],
    "dashboards/baby.html": [
        "Color index",
        "Green",
        "Blue",
        "Amber",
        "Red",
        "information only",
        "not a recommendation",
    ],
    "dashboards/stroller.html": [
        "Julie price board",
        "Purchase-worthy deals",
        "All leads ranked by price for Julie",
        "lowest to highest",
        "Message first",
        "Buy-worthy now",
        "Color index",
        "Green",
        "Blue",
        "Amber",
        "Red",
        "information only",
        "not a recommendation",
    ],
}


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
    required = REQUIRED_BY_FILE.get(str(path.relative_to(ROOT)), [])
    missing = [needle for needle in required if needle.lower() not in lowered]
    if missing:
        raise AssertionError(f"{path.relative_to(ROOT)} missing required public text: {missing}")


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


def check_live_url(url, expect_html=False):
    req = Request(url, headers={"User-Agent": "codex-public-dashboard-link-check/1.0"})
    with urlopen(req, timeout=20) as response:
        if response.status >= 400:
            raise AssertionError(f"{url} returned HTTP {response.status}")
        content_type = response.headers.get("content-type", "")
        if expect_html and "text/html" not in content_type.lower():
            raise AssertionError(f"{url} returned non-HTML content type: {content_type}")


def main():
    live_urls = set()
    for path in HTML_FILES:
        assert_no_forbidden_text(path)
        parser = LinkParser()
        parser.feed(path.read_text(encoding="utf-8"))
        for href in parser.hrefs:
            check_local_link(path, href)
            if href.startswith(("http://", "https://")):
                host = urlparse(href).netloc.lower()
                if host not in SKIP_LIVE_LINK_HOSTS:
                    live_urls.add(href)
    for url in sorted(live_urls):
        check_live_url(url)
    for url in PUBLIC_HTML_URLS:
        check_live_url(url, expect_html=True)
    print(f"verified {len(HTML_FILES)} html files, {len(live_urls)} external urls, and {len(PUBLIC_HTML_URLS)} public html urls")


if __name__ == "__main__":
    main()
