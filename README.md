# Main Deal Dashboard r0

Main dashboard hub for shareable daily tracker views.

Live site:

https://lukestambaugh75-hue.github.io/daily-dashboards-public-safe-r0/

There is no htmlpreview.github.io fallback any more, and there should not be one. That
proxy was a workaround from when this repo had no working Pages site. It does now, and
serves every page directly; routing through a third-party renderer only added a slower,
uglier URL that could break independently.

## Publishing

The pages under `dashboards/` and `index.html` are **generated**, not hand-written:

    python3 tools/publish_dashboards.py            # regenerate from live tracker data
    python3 tools/publish_dashboards.py --check    # fail if the committed pages are stale

Editing them by hand will be overwritten on the next run. They used to be hand-authored by
an agent on each run, which is why they drifted and stayed thin.

## Safety Boundary

This repo is intentionally public. Do not add private repo links, local file paths,
raw source ledgers, token usage details, exact trip details, internal company
content, ZIP/address references, or sensitive filenames.

The main page is a top-3 quality-and-price decision layer for Luke/Julie-safe
content. Every hub link stays inside this public-safe repository. Recipient-
specific trackers remain in separate repositories and have no runtime link,
asset, redirect, or source path from this hub.

## Included Public-Safe Views

- Main dashboard: top 3 public-safe quality-and-price picks.
- Washer Deal Tracker: sanitized decision and checkout-status view.
- Ford public-safe snapshot: sanitized market-summary view.
- Baby Gear Tracker: sanitized budget and category-summary view.
- Nuna Stroller Tracker: Julie-safe price and safety-decision view.

## Private Or Archived Views

- Token Cost Tracker: private but active. Use the private email attachment.
- Jackson/Yellowstone Weather Dashboard: archived/private-only.
- NextDecade dashboards: archived/private-only.
- Active Directory dashboard files: archived/private-only.
- Work Intake Governor dashboard: private-only.

## Verify

Run verification only from the canonical checkout at
`/Users/lukestambaugh/Documents/Files for GitHub/Public Safe Daily Dashboards r0`.
The verifier rejects any other path, a non-`main` branch, or the wrong GitHub
origin before checking dashboard content and links. Publishing scripts can use
`tools/canonical_checkout.py` with the stricter clean-tree and upstream-sync
options before writing.

The similarly named lowercase checkout is not a publishing target. Do not edit,
move, or delete it as part of dashboard refresh work.

```bash
/usr/bin/python3 tools/verify_links.py
```
