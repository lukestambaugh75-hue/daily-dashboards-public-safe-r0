import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify_links


class VerifyLinksPolicyTests(unittest.TestCase):
    def test_skips_amazon_live_checks_because_verifier_agent_gets_false_404(self):
        self.assertIn("www.amazon.com", verify_links.SKIP_LIVE_LINK_HOSTS)

    def test_exact_public_artifact_set_covers_all_pages_and_css(self):
        self.assertEqual(len(verify_links.PUBLIC_ARTIFACTS), 7)
        self.assertIn("dashboards/baby-stroller.html", verify_links.PUBLIC_ARTIFACTS)
        self.assertIn("styles.css", verify_links.PUBLIC_ARTIFACTS)

    @mock.patch.object(verify_links.subprocess, "run")
    def test_dirty_candidate_uses_committed_bytes_for_prepublication_check(self, run):
        run.side_effect = [
            mock.Mock(returncode=1),
            mock.Mock(returncode=0, stdout=b"published-bytes"),
        ]
        self.assertEqual(
            b"published-bytes",
            verify_links.expected_deployed_bytes("dashboards/stroller.html"),
        )
        self.assertEqual(
            [
                mock.call(
                    [
                        "git", "-C", str(verify_links.ROOT), "diff", "--quiet",
                        "--", "dashboards/stroller.html",
                    ],
                    check=False,
                ),
                mock.call(
                    [
                        "git", "-C", str(verify_links.ROOT), "show",
                        "HEAD:dashboards/stroller.html",
                    ],
                    check=False,
                    capture_output=True,
                ),
            ],
            run.call_args_list,
        )

    def test_default_main_does_not_check_retailer_liveness(self):
        with mock.patch.object(verify_links, "assert_canonical_checkout"), \
             mock.patch.object(verify_links, "check_live_url") as retailer, \
             mock.patch.object(verify_links, "check_live_artifact"):
            verify_links.main()
        retailer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
