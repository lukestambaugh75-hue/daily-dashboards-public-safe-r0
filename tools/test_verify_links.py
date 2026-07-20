import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify_links


class VerifyLinksPolicyTests(unittest.TestCase):
    def test_skips_amazon_live_checks_because_verifier_agent_gets_false_404(self):
        self.assertIn("www.amazon.com", verify_links.SKIP_LIVE_LINK_HOSTS)


if __name__ == "__main__":
    unittest.main()
