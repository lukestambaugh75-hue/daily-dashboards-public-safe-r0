#!/usr/bin/env python3
"""Verify public-safe dashboard links and obvious sensitive text leaks."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import time
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from canonical_checkout import assert_canonical_checkout

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [ROOT / "index.html", *sorted((ROOT / "dashboards").glob("*.html"))]
PUBLIC_SITE_BASE = "https://lukestambaugh75-hue.github.io/daily-dashboards-public-safe-r0"
PUBLIC_ARTIFACTS = [
    "index.html",
    "dashboards/washer.html",
    "dashboards/ford.html",
    "dashboards/baby.html",
    "dashboards/stroller.html",
    "dashboards/baby-stroller.html",
    "styles.css",
]
PUBLIC_ARTIFACTS_BY_SCOPE = {
    "all": PUBLIC_ARTIFACTS,
    "ford": ["dashboards/ford.html"],
    "baby": [
        "dashboards/baby.html",
        "dashboards/stroller.html",
        "dashboards/baby-stroller.html",
    ],
}
# Backward-compatible name for older tests/importers. The authoritative proof
# now covers every delivery page plus its shared stylesheet.
PUBLIC_HTML_URLS = [
    f"{PUBLIC_SITE_BASE}/{relative}"
    for relative in PUBLIC_ARTIFACTS
    if relative.endswith(".html")
]
SKIP_LIVE_LINK_HOSTS = {
    "facebook.com",
    "www.albeebaby.com",
    "www.amazon.com",
    "www.bloomingdales.com",
    "www.crateandbarrel.com",
    "www.ebay.com",
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
    "kegerator-tracker-r0",
    "ps5-tv-deal-tracker-r0",
    "devin.mullen89@gmail.com",
]
REQUIRED_BY_FILE = {
    "index.html": [
        "Top 3 Quality and Price",
        "Open public-safe view",
        "Raptor public-safe lead",
        "Washer checkout gate",
        "Nuna stroller price board",
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
        "Certified resale watchlist",
        "Good prices to keep tracking",
        "All leads ranked by price for Julie",
        "lowest to highest",
        "Message seller first",
        "Safe buy today",
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


class FragmentTargetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        element_id = attrs.get("id")
        if element_id:
            self.targets.add(element_id)
        if tag == "a" and attrs.get("name"):
            self.targets.add(attrs["name"])


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
    parsed = urlparse(href)
    if parsed.scheme in {"http", "https", "mailto"}:
        return
    local_path = unquote(parsed.path)
    target = source if not local_path else (source.parent / local_path).resolve()
    if not str(target).startswith(str(ROOT.resolve())):
        raise AssertionError(f"{source.relative_to(ROOT)} links outside repo: {href}")
    if not target.exists():
        raise AssertionError(f"{source.relative_to(ROOT)} broken local link: {href}")
    if parsed.fragment:
        parser = FragmentTargetParser()
        parser.feed(target.read_text(encoding="utf-8"))
        fragment = unquote(parsed.fragment)
        if fragment not in parser.targets:
            raise AssertionError(
                f"{source.relative_to(ROOT)} missing local fragment: {href}"
            )


def check_live_url(url, expect_html=False):
    req = Request(url, headers={"User-Agent": "codex-public-dashboard-link-check/1.0"})
    with urlopen(req, timeout=20) as response:
        if response.status >= 400:
            raise AssertionError(f"{url} returned HTTP {response.status}")
        content_type = response.headers.get("content-type", "")
        if expect_html and "text/html" not in content_type.lower():
            raise AssertionError(f"{url} returned non-HTML content type: {content_type}")


def expected_deployed_bytes(relative_path):
    """Return candidate bytes only when they are already committed.

    This verifier intentionally runs before publication.  For a dirty generated
    candidate, GitHub Pages can only be expected to serve the current HEAD;
    comparing it to the candidate would make a correct pre-push check fail.
    """
    local = ROOT / relative_path
    if not local.is_file():
        raise AssertionError(f"missing local public artifact: {relative_path}")
    diff = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--quiet", "--", relative_path],
        check=False,
    )
    if diff.returncode == 0:
        return local.read_bytes()
    if diff.returncode != 1:
        raise AssertionError(f"cannot determine Git state for public artifact: {relative_path}")
    committed = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"HEAD:{relative_path}"],
        check=False,
        capture_output=True,
    )
    if committed.returncode != 0:
        raise AssertionError(f"cannot read committed public artifact: {relative_path}")
    return committed.stdout


def check_live_artifact(relative_path):
    local = ROOT / relative_path
    if not local.is_file():
        raise AssertionError(f"missing local public artifact: {relative_path}")
    separator = "&" if "?" in relative_path else "?"
    url = (
        f"{PUBLIC_SITE_BASE}/{relative_path}{separator}"
        f"verify={int(time.time() * 1000)}"
    )
    req = Request(url, headers={
        "User-Agent": "codex-public-dashboard-byte-check/1.0",
        "Cache-Control": "no-cache",
    })
    with urlopen(req, timeout=20) as response:
        if response.status >= 400:
            raise AssertionError(f"{url} returned HTTP {response.status}")
        received = response.read()
    expected = expected_deployed_bytes(relative_path)
    if received != expected:
        raise AssertionError(
            f"live public artifact differs from deployed committed bytes: {relative_path}"
        )


def main(*, retailer_liveness=False, scope="all"):
    if scope not in PUBLIC_ARTIFACTS_BY_SCOPE:
        raise ValueError(f"unknown verification scope: {scope}")
    scoped_artifacts = PUBLIC_ARTIFACTS_BY_SCOPE[scope]
    scoped_html = [ROOT / relative for relative in scoped_artifacts if relative.endswith(".html")]
    assert_canonical_checkout(ROOT)
    live_urls = set()
    for path in scoped_html:
        assert_no_forbidden_text(path)
        parser = LinkParser()
        parser.feed(path.read_text(encoding="utf-8"))
        for href in parser.hrefs:
            check_local_link(path, href)
            if href.startswith(("http://", "https://")):
                host = urlparse(href).netloc.lower()
                if host not in SKIP_LIVE_LINK_HOSTS:
                    live_urls.add(href)
    if retailer_liveness:
        for url in sorted(live_urls):
            check_live_url(url)
    for relative_path in scoped_artifacts:
        check_live_artifact(relative_path)
    checked_external = len(live_urls) if retailer_liveness else 0
    print(
        f"verified {len(scoped_html)} html files, {checked_external} retailer urls, "
        f"and {len(scoped_artifacts)} exact public artifacts in {scope} scope"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--retailer-liveness",
        action="store_true",
        help="also check third-party retailer links; not part of deployment identity",
    )
    parser.add_argument(
        "--scope",
        choices=tuple(PUBLIC_ARTIFACTS_BY_SCOPE),
        default="all",
        help="limit local and deployed checks to one tracker lane",
    )
    args = parser.parse_args()
    main(retailer_liveness=args.retailer_liveness, scope=args.scope)
