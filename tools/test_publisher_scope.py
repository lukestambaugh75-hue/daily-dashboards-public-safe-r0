#!/usr/bin/env python3
import unittest
from pathlib import Path
from unittest import mock

import publish_dashboards


class PublisherScopeTests(unittest.TestCase):
    def test_ford_scope_only_builds_ford_and_never_reads_baby(self):
        ford_html = "<html>Ford</html>"
        with mock.patch.object(publish_dashboards, "build_ford", return_value=(ford_html, {})) as ford, \
             mock.patch.object(publish_dashboards, "build_baby", side_effect=AssertionError("Baby was read")) as baby:
            targets = publish_dashboards.build_targets("ford")
        self.assertEqual(
            [(Path(publish_dashboards.ROOT) / "dashboards" / "ford.html", ford_html)],
            targets,
        )
        ford.assert_called_once_with()
        baby.assert_not_called()

    def test_baby_scope_owns_baby_pages_but_not_ford_or_index(self):
        with mock.patch.object(publish_dashboards, "build_baby", return_value=("<html>Baby</html>", {})), \
             mock.patch.object(publish_dashboards, "build_baby_stroller", return_value="<html>Combined</html>"):
            targets = publish_dashboards.build_targets("baby")
        self.assertEqual(
            [
                Path(publish_dashboards.ROOT) / "dashboards" / "baby.html",
                Path(publish_dashboards.ROOT) / "dashboards" / "baby-stroller.html",
            ],
            [path for path, _html in targets],
        )

    def test_generac_scope_imports_only_the_tracker_owned_public_artifact(self):
        with mock.patch.object(publish_dashboards, "build_generac", return_value="<html>Generac</html>") as generac, \
             mock.patch.object(publish_dashboards, "build_ford", side_effect=AssertionError("Ford was read")):
            targets = publish_dashboards.build_targets("generac")
        self.assertEqual(
            [(Path(publish_dashboards.ROOT) / "dashboards" / "generac.html", "<html>Generac</html>")],
            targets,
        )
        generac.assert_called_once_with()

    def test_all_scope_remains_explicit_full_hub_mode(self):
        with mock.patch.object(publish_dashboards, "build_ford", return_value=("ford", {})), \
             mock.patch.object(publish_dashboards, "build_washer", return_value=("washer", {})), \
             mock.patch.object(publish_dashboards, "build_baby", return_value=("baby", {})), \
             mock.patch.object(publish_dashboards, "build_baby_stroller", return_value="stroller"), \
             mock.patch.object(publish_dashboards, "build_generac", return_value="generac"), \
             mock.patch.object(publish_dashboards, "build_index", return_value="index"):
            targets = publish_dashboards.build_targets("all")
        self.assertEqual(6, len(targets))
        self.assertEqual("index.html", targets[-1][0].name)


if __name__ == "__main__":
    unittest.main()
