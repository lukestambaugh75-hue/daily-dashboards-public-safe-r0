#!/usr/bin/env python3
"""Tests for the canonical public-dashboard checkout guard."""

import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("canonical_checkout.py")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import canonical_checkout
import verify_links


def valid_state(**changes):
    state = canonical_checkout.CheckoutState(
        root=canonical_checkout.CANONICAL_ROOT,
        origin=canonical_checkout.EXPECTED_ORIGIN,
        branch="main",
        dirty=False,
        head="abc123",
        upstream="abc123",
    )
    return state._replace(**changes)


class CanonicalCheckoutContractTests(unittest.TestCase):
    def test_module_exposes_required_contract(self):
        self.assertTrue(
            MODULE_PATH.exists(),
            "tools/canonical_checkout.py must provide the checkout guard",
        )
        spec = importlib.util.spec_from_file_location("canonical_checkout", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertTrue(hasattr(module, "CANONICAL_ROOT"))
        self.assertTrue(hasattr(module, "EXPECTED_ORIGIN"))
        self.assertTrue(hasattr(module, "CheckoutState"))
        self.assertTrue(callable(getattr(module, "collect_checkout_state", None)))
        self.assertTrue(callable(getattr(module, "assert_checkout_state", None)))
        self.assertTrue(callable(getattr(module, "assert_canonical_checkout", None)))


class CanonicalCheckoutStateTests(unittest.TestCase):
    def test_rejects_lowercase_duplicate_path_without_reading_git(self):
        duplicate = Path(
            "/Users/lukestambaugh/Documents/Files for GitHub/daily-dashboards-public-safe-r0"
        )
        original = canonical_checkout.collect_checkout_state

        def unexpected_collection(root):
            self.fail(f"must not inspect noncanonical checkout: {root}")

        canonical_checkout.collect_checkout_state = unexpected_collection
        try:
            with self.assertRaisesRegex(RuntimeError, "canonical"):
                canonical_checkout.assert_canonical_checkout(duplicate)
        finally:
            canonical_checkout.collect_checkout_state = original

    def test_rejects_wrong_origin(self):
        with self.assertRaisesRegex(RuntimeError, "origin"):
            canonical_checkout.assert_checkout_state(
                valid_state(origin="https://github.com/example/wrong.git")
            )

    def test_rejects_non_main_branch(self):
        with self.assertRaisesRegex(RuntimeError, "main"):
            canonical_checkout.assert_checkout_state(valid_state(branch="feature"))

    def test_rejects_dirty_tree_only_when_clean_is_required(self):
        state = valid_state(dirty=True)

        canonical_checkout.assert_checkout_state(state)
        with self.assertRaisesRegex(RuntimeError, "clean"):
            canonical_checkout.assert_checkout_state(state, require_clean=True)

    def test_rejects_mismatched_head_and_upstream_only_when_sync_is_required(self):
        state = valid_state(upstream="def456")

        canonical_checkout.assert_checkout_state(state)
        with self.assertRaisesRegex(RuntimeError, "upstream"):
            canonical_checkout.assert_checkout_state(
                state,
                require_upstream_sync=True,
            )

    def test_rejects_missing_upstream_when_sync_is_required(self):
        with self.assertRaisesRegex(RuntimeError, "upstream"):
            canonical_checkout.assert_checkout_state(
                valid_state(upstream=None),
                require_upstream_sync=True,
            )

    def test_accepts_valid_canonical_state(self):
        canonical_checkout.assert_checkout_state(
            valid_state(),
            require_clean=True,
            require_upstream_sync=True,
        )

    def test_collects_repository_state_through_injected_git_runner(self):
        responses = {
            ("remote", "get-url", "origin"): canonical_checkout.EXPECTED_ORIGIN,
            ("branch", "--show-current"): "main",
            ("status", "--porcelain"): " M dashboards/ford.html",
            ("rev-parse", "HEAD"): "abc123",
            ("rev-parse", "@{upstream}"): "abc123",
        }
        calls = []

        def fake_git(root, args):
            calls.append((root, tuple(args)))
            return responses[tuple(args)]

        state = canonical_checkout.collect_checkout_state(
            canonical_checkout.CANONICAL_ROOT,
            run_git=fake_git,
        )

        self.assertEqual(canonical_checkout.CANONICAL_ROOT, state.root)
        self.assertEqual(canonical_checkout.EXPECTED_ORIGIN, state.origin)
        self.assertEqual("main", state.branch)
        self.assertTrue(state.dirty)
        self.assertEqual("abc123", state.head)
        self.assertEqual("abc123", state.upstream)
        self.assertEqual(5, len(calls))

    def test_collection_records_missing_upstream_without_live_git(self):
        responses = {
            ("remote", "get-url", "origin"): canonical_checkout.EXPECTED_ORIGIN,
            ("branch", "--show-current"): "main",
            ("status", "--porcelain"): "",
            ("rev-parse", "HEAD"): "abc123",
        }

        def fake_git(root, args):
            if tuple(args) == ("rev-parse", "@{upstream}"):
                raise subprocess.CalledProcessError(128, ["git", *args])
            return responses[tuple(args)]

        state = canonical_checkout.collect_checkout_state(
            canonical_checkout.CANONICAL_ROOT,
            run_git=fake_git,
        )

        self.assertIsNone(state.upstream)


class VerifyLinksGuardTests(unittest.TestCase):
    def test_main_checks_canonical_checkout_before_link_verification(self):
        events = []
        original_guard = getattr(verify_links, "assert_canonical_checkout", None)
        original_files = verify_links.HTML_FILES
        original_urls = verify_links.PUBLIC_HTML_URLS
        verify_links.assert_canonical_checkout = lambda root: events.append(root)
        verify_links.HTML_FILES = []
        verify_links.PUBLIC_HTML_URLS = []
        try:
            verify_links.main()
        finally:
            verify_links.HTML_FILES = original_files
            verify_links.PUBLIC_HTML_URLS = original_urls
            if original_guard is None:
                del verify_links.assert_canonical_checkout
            else:
                verify_links.assert_canonical_checkout = original_guard

        self.assertEqual([verify_links.ROOT], events)


if __name__ == "__main__":
    unittest.main()
