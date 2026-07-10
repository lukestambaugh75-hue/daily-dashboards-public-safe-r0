#!/usr/bin/env python3
"""Reject publication work outside the canonical public-dashboard checkout."""

from pathlib import Path
import subprocess
from typing import Callable, NamedTuple, Optional, Sequence


CANONICAL_ROOT = Path(
    "/Users/lukestambaugh/Documents/Files for GitHub/Public Safe Daily Dashboards r0"
)
EXPECTED_ORIGIN = "https://github.com/lukestambaugh75-hue/daily-dashboards-public-safe-r0.git"


class CheckoutState(NamedTuple):
    root: Path
    origin: str
    branch: str
    dirty: bool
    head: str
    upstream: Optional[str]


GitRunner = Callable[[Path, Sequence[str]], str]


def collect_checkout_state(
    root: Path,
    *,
    run_git: Optional[GitRunner] = None,
) -> CheckoutState:
    resolved_root = Path(root).expanduser().resolve(strict=False)

    def default_git(command_root: Path, args: Sequence[str]) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(command_root),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return completed.stdout.strip()

    git = run_git or default_git
    try:
        upstream = git(resolved_root, ("rev-parse", "@{upstream}"))
    except subprocess.CalledProcessError:
        upstream = None

    return CheckoutState(
        root=resolved_root,
        origin=git(resolved_root, ("remote", "get-url", "origin")),
        branch=git(resolved_root, ("branch", "--show-current")),
        dirty=bool(git(resolved_root, ("status", "--porcelain"))),
        head=git(resolved_root, ("rev-parse", "HEAD")),
        upstream=upstream,
    )


def assert_checkout_state(
    state: CheckoutState,
    *,
    require_clean: bool = False,
    require_upstream_sync: bool = False,
) -> None:
    canonical_root = CANONICAL_ROOT.resolve(strict=False)
    actual_root = state.root.expanduser().resolve(strict=False)
    if actual_root != canonical_root:
        raise RuntimeError(
            f"Refusing noncanonical checkout {actual_root}; canonical checkout is {canonical_root}"
        )
    if state.origin != EXPECTED_ORIGIN:
        raise RuntimeError(
            f"Unexpected origin {state.origin!r}; expected {EXPECTED_ORIGIN!r}"
        )
    if state.branch != "main":
        raise RuntimeError(f"Expected main branch; found {state.branch!r}")
    if require_clean and state.dirty:
        raise RuntimeError("Canonical checkout must be clean for this operation")
    if require_upstream_sync:
        if state.upstream is None:
            raise RuntimeError("Canonical checkout has no upstream branch")
        if state.head != state.upstream:
            raise RuntimeError(
                f"Canonical checkout HEAD {state.head} does not match upstream {state.upstream}"
            )


def assert_canonical_checkout(
    root: Path,
    *,
    require_clean: bool = False,
    require_upstream_sync: bool = False,
) -> None:
    resolved_root = Path(root).expanduser().resolve(strict=False)
    canonical_root = CANONICAL_ROOT.resolve(strict=False)
    if resolved_root != canonical_root:
        raise RuntimeError(
            f"Refusing noncanonical checkout {resolved_root}; canonical checkout is {canonical_root}"
        )
    assert_checkout_state(
        collect_checkout_state(resolved_root),
        require_clean=require_clean,
        require_upstream_sync=require_upstream_sync,
    )
