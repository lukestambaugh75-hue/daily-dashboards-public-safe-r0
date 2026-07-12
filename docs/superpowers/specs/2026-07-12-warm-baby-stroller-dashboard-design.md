# Warm Baby + Stroller Dashboard Design

**Date:** 2026-07-12
**Status:** Design approved in conversation; written-spec review pending
**Audience:** Luke and Julie
**Primary surface:** Public-safe Baby + Stroller dashboard

## Goal

Redesign the combined Baby + Stroller dashboard into a calm, warm family-planning experience that answers “what should we do next?” before exposing the full research detail.

The visual direction is Apple-inspired in its restraint and hierarchy: clear typography, generous space, quiet surfaces, direct language, and one obvious decision path. It must not copy Apple logos, product marks, proprietary assets, or exact Apple UI.

## Current problem

The current combined page is functionally correct but still reads like two generated tracker pages placed together. It exposes dense deal grids and long sections before establishing a simple decision. The page needs a single family-level overview, a clear stroller fallback, and a calmer transition into baby-gear details.

## Design direction

### Visual language

- Warm ivory page background with sandstone and muted brown accents.
- Charcoal text with restrained green for safe/recommended states.
- Minimal borders and no decorative card grid around every item.
- System sans typography with a compact editorial scale.
- Rounded controls only where they communicate an active choice.
- No gradients, neon accents, dark dashboard chrome, or excessive badges.

### Top-of-page hierarchy

1. Small context line: “Our baby list · shared with Luke + Julie”.
2. Main headline: “One calm view of what’s next.”
3. Two primary metrics:
   - Best new stroller price: current safe-new price, currently `$800`.
   - Registry verified: current verified/expected count, currently `145/212`.
4. Short supporting sentence explaining that stroller price is primary while safety determines whether a lead is usable.
5. One segmented control with two states: `Stroller` and `Baby gear`.

### Stroller state

The default state is Stroller because the current user goal is an active purchase decision.

- Section title: “Worth looking at”.
- First row: lowest purchase-worthy lead, currently `$650`, labeled “Verify car seat before buying”.
- Second row: safe new fallback, currently `$800`, labeled “Granite · new · safe fallback”.
- Each row uses a single price, short source label, status sentence, and one action link.
- The full purchase-worthy list, certified resale watchlist, price ladder, and safety checklist remain below the decision layer.

### Baby gear state

- Show registry coverage and purchase progress first.
- Show a compact “Still needed” summary before long tables.
- Preserve exact freshness, partial-run, blocked-source, and safety language.
- Move detailed registry evidence into expandable or lower-page sections without removing it.

### Interaction

- The segmented control changes the visible summary layer with native buttons and `aria-pressed` state.
- The selected state must be visible without relying on color alone.
- Keyboard users can move between the two states and see focus clearly.
- The page remains useful with JavaScript disabled: the default stroller summary and all lower content remain visible.

## Data and safety requirements

- Continue reading stroller data from `Baby Prep r0/data/stroller_tracker.json` and baby/registry data from the existing public-publisher inputs.
- Preserve the current price-first ordering: lower price can outrank preferred Granite color, but used car-seat safety remains a separate gate.
- Do not expose private registry URLs, local paths, email addresses, raw ledgers, or private source identifiers.
- Keep the public-safe dashboard as the single shareable delivery URL: `dashboards/baby-stroller.html`.
- Keep legacy `dashboards/baby.html` and `dashboards/stroller.html` generated for compatibility, but remove them from the primary public hub and email delivery path.

## Implementation scope

### Public Safe Daily Dashboards r0

- Update `tools/publish_dashboards.py` to generate the warm combined dashboard structure and data-driven summary.
- Update `styles.css` with warm tokens, typography, spacing, segmented-control, row, and responsive rules.
- Regenerate `dashboards/baby-stroller.html` and `index.html`.
- Update public-safe tests for the new hierarchy, single delivery surface, accessibility, and forbidden-content rules.

### Baby Prep r0

- Keep the combined email renderer pointed at the single public dashboard URL.
- Preserve the existing email-safe plain-text and HTML link contract.
- Do not change the underlying price research, freshness gates, or recipient authorization.

## Verification

- Public publisher regeneration produces a deterministic combined page.
- Public audience-segregation tests pass.
- Public link verifier passes with the new page and no forbidden links.
- Baby Prep unit tests and validation pass.
- Live GitHub Pages page shows the warm summary, current `$800` safe-new price, current registry coverage, and working Stroller/Baby gear control.
- Mobile layout is checked at narrow width for readable rows, no horizontal overflow, and visible focus states.

## Open decisions resolved

- One combined dashboard is the primary surface; separate baby/stroller pages are legacy compatibility outputs.
- Stroller is the default first view because it contains the active buying decision.
- The visual system is warm family planning, not dark dashboard chrome or a generic analytics grid.
