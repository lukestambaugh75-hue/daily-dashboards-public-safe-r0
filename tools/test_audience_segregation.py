import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = [
    ROOT / "index.html",
    ROOT / "styles.css",
    *sorted((ROOT / "dashboards").glob("*.html")),
]
FORBIDDEN_DEVIN_RUNTIME = (
    "kegerator-tracker-r0",
    "ps5-tv-deal-tracker-r0",
    "devin.mullen89@gmail.com",
)


class RuntimeLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(href)


class AudienceSegregationTests(unittest.TestCase):
    def test_public_safe_runtime_has_no_devin_surface_links(self):
        for path in RUNTIME_FILES:
            text = path.read_text(encoding="utf-8").lower()
            for forbidden in FORBIDDEN_DEVIN_RUNTIME:
                with self.subTest(path=path.name, forbidden=forbidden):
                    self.assertNotIn(forbidden, text)

    def test_hub_top_actions_and_top_picks_use_only_local_public_safe_views(self):
        text = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn('href="dashboards/ford.html"', text)
        self.assertIn('href="dashboards/washer.html"', text)
        self.assertIn('href="dashboards/stroller.html"', text)
        self.assertIn("Raptor public-safe lead", text)
        self.assertIn("Washer checkout gate", text)
        self.assertIn("Nuna stroller price board", text)
        self.assertNotIn("Outdoor keg value", text)
        self.assertNotIn("PS5 and TV stack", text)

        parser = RuntimeLinkParser()
        parser.feed(text)
        for href in parser.hrefs:
            parsed = urlparse(href)
            with self.subTest(href=href):
                if parsed.scheme:
                    self.assertEqual(parsed.scheme, "https")
                    self.assertEqual(
                        parsed.netloc, "lukestambaugh75-hue.github.io"
                    )
                    self.assertTrue(
                        parsed.path.startswith(
                            "/daily-dashboards-public-safe-r0/"
                        )
                    )
                else:
                    self.assertEqual(parsed.netloc, "")
                    self.assertFalse(parsed.path.startswith(("/", "\\")))
                    self.assertNotIn("..", Path(parsed.path).parts)
                    self.assertTrue(parsed.path.startswith("dashboards/"))

    def test_runtime_has_no_email_mailto_or_local_path_leaks(self):
        for path in RUNTIME_FILES:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotRegex(text, r"(?i)mailto:")
                self.assertNotRegex(text, r"(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}")
                self.assertNotRegex(text, r"(?i)(?:file://|/users/|[a-z]:\\)")

    def test_mobile_table_layout_is_bounded_to_the_hub_viewport(self):
        css = (ROOT / "styles.css").read_text(encoding="utf-8")

        self.assertIn("table-layout: fixed", css)
        self.assertIn("overflow-wrap: anywhere", css)

    def test_mobile_pick_card_cta_accounts_for_horizontal_margins(self):
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        blocks = re.findall(r"\.pick-card \.button\s*\{([^}]*)\}", css, re.S)
        self.assertTrue(blocks, "expected a mobile pick-card button rule")
        mobile = blocks[-1]
        self.assertIn("margin: 8px 16px 16px", mobile)
        self.assertIn("width: calc(100% - 32px)", mobile)


if __name__ == "__main__":
    unittest.main()
