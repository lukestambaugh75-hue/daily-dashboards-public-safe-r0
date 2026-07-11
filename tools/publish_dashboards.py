#!/usr/bin/env python3
"""Generate the public-safe dashboards and the hub index from live tracker data.

    python3 tools/publish_dashboards.py            # regenerate everything
    python3 tools/publish_dashboards.py --check    # fail if the committed files are stale

Why this exists: the public-safe pages used to be hand-written by an agent on every run.
They drifted, and they stayed thin -- 3.4 KB of static summary next to a 300 KB private
dashboard -- so the one link that *did* work felt like it showed nothing. This renders
them deterministically from the same data the trackers already produce, so the public
pages are as rich as the data allows and can never go stale.

Public-safe means, and this is enforced by tools/test_audience_segregation.py:
  * no financing detail, no credit score, no local file paths, no email addresses
  * no exact source-ledger links (no per-listing dealer URLs)
  * no PS5/kegerator surface -- those are a different audience and must not appear here

Charts are inline SVG. That is fine here and NOT fine in the emails: this is a browser,
which renders SVG; a mail client does not. The email path uses PNGs instead.
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKERS = Path.home() / "Documents" / "Files for GitHub"

FORD = TRACKERS / "Ford Raptor Tracker r0"
WASHER = TRACKERS / "Washing Machine Deal Finder r0"
BABY = TRACKERS / "Baby Prep r0"

BLUE, GREEN, AMBER, RED = "#2563eb", "#059669", "#d97706", "#dc2626"


# ------------------------------------------------------------------ helpers

def money(v, k=False):
    if v is None:
        return "--"
    if k and abs(v) >= 1000:
        return f"${v/1000:,.1f}k"
    return f"${round(v):,}"


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def identity_attrs(private_index):
    """Carry the tracker's deployment-identity attributes onto the public page.

    The private dashboard stamps its <body> with data-snapshot-id / data-refresh-at /
    data-row-count / data-published-at, and the tracker's check_public_pages.py compares
    those against the live page to prove it is not serving stale data. That freshness
    guarantee is worth keeping now that the public page is the only one published, so we
    copy the attributes across verbatim rather than reimplementing the hashing here.
    """
    try:
        # Read the whole file: the tracker inlines its CSS, so <body> can sit well past
        # any fixed-size prefix (it is ~13 KB into Ford's 300 KB dashboard).
        head = Path(private_index).read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"<body([^>]*)>", head)
    if not m:
        return ""
    keep = re.findall(
        r'(data-(?:snapshot-id|refresh-at|row-count|published-at)="[^"]*")', m.group(1)
    )
    return (" " + " ".join(keep)) if keep else ""


def read_csv(path, tail=None):
    try:
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
    except OSError:
        return []
    return rows[-tail:] if tail else rows


def num(row, key, cast=float):
    try:
        return cast(row[key])
    except (KeyError, TypeError, ValueError):
        return None


def sparkline(points, color=BLUE, width=520, height=110, money_axis=True):
    """Inline SVG line chart. Browsers render this natively; no image files needed."""
    pts = [p for p in points if p is not None]
    if len(pts) < 2:
        return ""
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1
    pad = 8
    step = (width - 2 * pad) / (len(pts) - 1)

    coords = [
        (pad + i * step, height - pad - ((v - lo) / span) * (height - 2 * pad))
        for i, v in enumerate(pts)
    ]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    area = f"{coords[0][0]:.1f},{height - pad} " + line + f" {coords[-1][0]:.1f},{height - pad}"
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{color}" />'
        for x, y in coords
    )
    fmt = (lambda v: money(v, k=True)) if money_axis else (lambda v: f"{v:,.0f}")

    return f"""<svg viewBox="0 0 {width} {height}" width="100%" height="{height}"
     role="img" aria-label="trend" style="display:block;max-width:100%">
  <polygon points="{area}" fill="{color}" opacity="0.08" />
  <polyline points="{line}" fill="none" stroke="{color}" stroke-width="2.5"
            stroke-linejoin="round" stroke-linecap="round" />
  {dots}
  <text x="{pad}" y="12" font-size="11" fill="#64748b">{fmt(hi)}</text>
  <text x="{pad}" y="{height - 1}" font-size="11" fill="#64748b">{fmt(lo)}</text>
</svg>"""


def bar(label, value_text, pct, tone=""):
    pct = max(2, min(100, pct))
    return (f'<div class="bar-row"><div class="bar-label">{label}</div>'
            f'<div class="bar-track"><div class="bar-fill {tone}" '
            f'style="width: {pct:.0f}%"></div></div>'
            f'<div class="bar-value">{value_text}</div></div>')


def page(title, eyebrow, headline, lead, sections, footer, body_attrs=""):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body{body_attrs}>
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow">{eyebrow}</p>
      <h1>{headline}</h1>
      <p class="lead">{lead}</p>
      <div class="top-actions">
        <a class="button primary" href="../index.html">Back to hub</a>
      </div>
      <div class="callout color-index">
        <strong>Color index.</strong>
        <p><strong>Green</strong> = recommended or ready to act. <strong>Blue</strong> = information only, like links, charts, totals, or neutral controls; it is not a recommendation. <strong>Amber</strong> = caution; check details before acting. <strong>Red</strong> = blocked or stop; do not act until fixed.</p>
      </div>
    </div>
  </header>
  <main>
{sections}
  </main>
  <footer class="footer">
    <div class="wrap">{footer}</div>
  </footer>
</body>
</html>
"""


def section(inner):
    return f'    <section class="section">\n      <div class="wrap">\n{inner}\n      </div>\n    </section>\n'


def metrics(items):
    cells = "".join(
        f'<div class="metric"><span class="meta">{k}</span><strong>{v}</strong></div>'
        for k, v in items
    )
    return f'        <div class="metric-row">{cells}</div>'


# ------------------------------------------------------------------- FORD

def build_ford():
    data = read_json(FORD / "data" / "listings.json")
    if not data:
        return None, {}
    s = data["summary"]
    listings = [x for x in data.get("listings", []) if x.get("price")]
    prices = sorted(x["price"] for x in listings)
    if not prices:
        return None, {}
    median = prices[len(prices) // 2]
    hist = read_csv(FORD / "history.csv", tail=21)

    # The refresh timestamp lives in the lead paragraph, not a metric tile -- it is far
    # longer than the other values and wrapped the tile row onto a second line.
    secs = [section(metrics([
        ("Eligible leads", s["eligible_count"]),
        ("Lowest visible", money(s["cheapest_price"])),
        ("Median visible", money(median)),
        ("Newly listed", s.get("newly_listed_count", 0)),
    ]))]

    # Price trend -- aggregate only, so it stays public-safe.
    lows = [num(r, "cheapest_price") for r in hist]
    meds = [num(r, "median_price") for r in hist]
    charts = ""
    if len([p for p in lows if p]) >= 2:
        charts = (
            f'          <article class="panel chart">\n'
            f'            <h2>Lowest visible price, last {len(hist)} days</h2>\n'
            f'            {sparkline(lows, GREEN)}\n'
            f'          </article>\n'
            f'          <article class="panel chart">\n'
            f'            <h2>Median visible price, last {len(hist)} days</h2>\n'
            f'            {sparkline(meds, BLUE)}\n'
            f'          </article>\n'
        )
        secs.append(section(f'        <div class="grid two">\n{charts}        </div>'))

    # Price band + market split.
    hi = prices[-1]
    band = (
        '          <article class="panel chart">\n            <h2>Price Band</h2>\n'
        + bar("Lowest visible", money(prices[0], k=True), 100 * prices[0] / hi)
        + bar("Median visible", money(median, k=True), 100 * median / hi, "amber")
        + bar("Highest allowed", money(hi, k=True), 100, "red")
        + "          </article>\n"
    )
    counts = s.get("market_counts") or {}
    peak = max(counts.values()) if counts else 1
    market = (
        '          <article class="panel chart">\n            <h2>Coverage by market</h2>\n'
        + "".join(
            bar(k.replace(" 5-hour radius", ""), str(v), 100 * v / peak)
            for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
        )
        + f'            <p class="meta">{data["generated_label"]}. '
          f'Dealer confirmation is still required for availability, final price, fees, '
          f'mileage, and add-ons before acting.</p>\n'
          '          </article>\n'
    )
    secs.append(section(f'        <div class="grid two">\n{band}{market}        </div>'))

    html = page(
        "Ford Raptor Tracker - Public Safe",
        "Ford Raptor Tracker",
        f"{s['eligible_count']} eligible leads in the current public marketplace scan.",
        f"Refreshed {data['generated_label']}. Public-safe market summary: this page "
        "excludes private location assumptions, financing details, exact source-ledger "
        "links, and local file paths.",
        "".join(secs),
        "Sanitized summary only. The private tracker keeps full source rows, raw listing "
        "links, and loan assumptions out of this public page.",
        body_attrs=identity_attrs(FORD / "index.html"),
    )
    return html, {
        "price": money(s["cheapest_price"]),
        "count": s["eligible_count"],
        "label": data["generated_label"],
    }


# ----------------------------------------------------------------- WASHER

def build_washer():
    data = read_json(WASHER / "data" / "deals.json")
    if not data:
        return None, {}
    m = data.get("summary_metrics") or {}
    hist = read_csv(WASHER / "history.csv", tail=21)
    verdict = (hist[-1].get("verdict") if hist else "Hold") or "Hold"

    secs = [section(metrics([
        ("Recommended", m.get("recommended_count", "--")),
        ("Best savings", money(m.get("best_supported_savings"))),
        ("Average savings", money(m.get("average_supported_savings"))),
        ("Verdict", verdict),
    ]))]

    savings = [num(r, "best_savings_usd") for r in hist]
    if len([x for x in savings if x]) >= 2:
        secs.append(section(
            f'        <article class="panel chart">\n'
            f'          <h2>Best supported savings, last {len(hist)} days</h2>\n'
            f'          {sparkline(savings, GREEN)}\n'
            f'        </article>'
        ))

    gate = (
        '        <article class="panel chart">\n          <h2>Decision gate</h2>\n'
        '          <div class="callout">\n'
        '            <strong>Hold until the delivered total is proven.</strong>\n'
        '            <p class="meta">Public item-page pricing is not enough. Compare '
        'delivered checkout terms, taxes, fees, haul-away, and install before treating '
        'any pair as a buy.</p>\n          </div>\n'
    )
    rec = data.get("direct_recommendation") or {}
    if rec.get("summary"):
        gate += (f'          <table class="table"><tbody>'
                 f'<tr><td>Best first call</td><td>{rec.get("model", "--")}</td></tr>'
                 f'<tr><td>Why</td><td>{rec["summary"]}</td></tr>')
        if rec.get("why_not_perfect"):
            gate += f'<tr><td>Caveat</td><td>{rec["why_not_perfect"]}</td></tr>'
        gate += "</tbody></table>\n"
    gate += "        </article>\n"
    secs.append(section(gate))

    html = page(
        "Washer Deal Tracker - Public Safe",
        "Washer Deal Tracker",
        f"{m.get('recommended_count', 0)} recommended models, best supported saving "
        f"{money(m.get('best_supported_savings'))}.",
        "Public-safe decision view. Detailed checkout evidence, cart state, and local "
        "source ledgers stay private.",
        "".join(secs),
        "Sanitized summary only. Confirm delivered total, taxes, fees, haul-away, and "
        "install before buying.",
    )
    return html, {"price": money(m.get("best_supported_savings")), "verdict": verdict}


# ------------------------------------------------------------------- BABY

def build_baby():
    gear = read_json(BABY / "data" / "gear.json")
    reg = read_json(BABY / "data" / "registry.json")
    if not gear:
        return None, {}

    items = gear.get("price_items", [])
    priced = [i for i in items if i.get("mid_new_price_usd")]
    total_new = sum(i["mid_new_price_usd"] for i in priced)

    reg_items = (reg or {}).get("registry_items", [])
    requested = sum(i.get("qty_requested", 0) or 0 for i in reg_items)
    purchased = sum(i.get("qty_purchased", 0) or 0 for i in reg_items)
    pct = (100 * purchased / requested) if requested else 0

    secs = [section(metrics([
        ("Gear items tracked", len(items)),
        ("Mid-tier new total", money(total_new)),
        ("Registry items", len(reg_items)),
        ("Registry purchased", f"{purchased} of {requested}"),
    ]))]

    progress = (
        '          <article class="panel chart">\n            <h2>Registry progress</h2>\n'
        + bar("Purchased", f"{pct:.0f}%", pct, "" if pct >= 50 else "amber")
        + bar("Remaining", f"{max(0, requested - purchased)} items", 100 - pct, "amber")
        + '            <p class="meta">Arrival January 2027. Counts come from the '
          'signed-in registry reconciliation.</p>\n          </article>\n'
    )

    # Biggest-ticket categories -- aggregate, no purchase links.
    top = sorted(priced, key=lambda i: -i["mid_new_price_usd"])[:6]
    peak = top[0]["mid_new_price_usd"] if top else 1
    spend = (
        '          <article class="panel chart">\n            <h2>Biggest-ticket gear</h2>\n'
        + "".join(
            bar(i["item"], money(i["mid_new_price_usd"]),
                100 * i["mid_new_price_usd"] / peak,
                "amber" if i.get("buy_used_caution") else "")
            for i in top
        )
        + '            <p class="meta">Amber marks items flagged not to buy used on '
          'safety grounds.</p>\n          </article>\n'
    )
    secs.append(section(f'        <div class="grid two">\n{progress}{spend}        </div>'))

    caution = [i for i in items if i.get("buy_used_caution")]
    if caution:
        rows = "".join(
            f'<tr><td>{i["item"]}</td><td>{i.get("caution_reason", "Do not buy used.")}</td></tr>'
            for i in caution
        )
        secs.append(section(
            '        <article class="panel chart">\n'
            '          <h2>Do not buy these used</h2>\n'
            f'          <table class="table"><tbody>{rows}</tbody></table>\n'
            '        </article>'
        ))

    html = page(
        "Baby Gear Tracker - Public Safe",
        "Baby Gear Tracker",
        f"{len(items)} gear items tracked, {purchased} of {requested} registry items purchased.",
        "Budget and category snapshot. The detailed local workbook, registry links, and "
        "resale ledgers stay private.",
        "".join(secs),
        "Sanitized summary only. Safety-critical items should be bought new; confirm "
        "recalls and expiry dates before accepting any used gear.",
    )
    return html, {"purchased": purchased, "requested": requested}


# ------------------------------------------------------------------- INDEX

def build_index(ford, washer, baby, stroller_price="$600"):
    today = datetime.now().strftime("%B %-d, %Y")
    ford_price = ford.get("price", "--")
    washer_verdict = washer.get("verdict", "Hold")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Main Deal Dashboard</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow">Main dashboard</p>
      <h1>Top 3 Quality and Price picks.</h1>
      <p class="lead">A quick public-safe decision board for Luke and Julie. Recipient-specific trackers are intentionally absent from this hub and from its runtime links.</p>
      <div class="top-actions">
        <a class="button primary" href="dashboards/ford.html">Open Raptor summary</a>
        <a class="button" href="dashboards/washer.html">Open Washer summary</a>
        <a class="button" href="dashboards/stroller.html">Open Stroller board</a>
        <a class="button" href="dashboards/baby.html">Open Baby gear</a>
      </div>
      <div class="callout color-index">
        <strong>Color index.</strong>
        <p><strong>Green</strong> = recommended or ready to act. <strong>Blue</strong> = information only, like links, charts, totals, or neutral controls; it is not a recommendation. <strong>Amber</strong> = caution; check details before acting. <strong>Red</strong> = blocked or stop; do not act until fixed.</p>
      </div>
      <div class="top-picks">
        <article class="pick-card raptor-card">
          <div class="pick-media" aria-hidden="true"></div>
          <div>
            <div class="pick-top">
              <span class="pick-rank">1</span>
              <span class="pick-label">Raptor public-safe lead</span>
            </div>
            <strong class="pick-value">{ford_price}</strong>
            <h2>Lowest qualifying Ford F-150 Raptor</h2>
            <p class="meta">{ford.get('count', 0)} eligible leads: 4 full doors, under 10,000 miles, under the $100,000 cap. Refreshed {ford.get('label', today)}.</p>
            <div class="sub-links">
              <a href="dashboards/ford.html">Price trend</a>
              <a href="dashboards/ford.html">Price band</a>
              <a href="dashboards/ford.html">Market read</a>
            </div>
          </div>
          <a class="button primary" href="dashboards/ford.html">Open public-safe view</a>
        </article>
        <article class="pick-card washer-card">
          <div class="pick-media" aria-hidden="true"></div>
          <div>
            <div class="pick-top">
              <span class="pick-rank">2</span>
              <span class="pick-label">Washer checkout gate</span>
            </div>
            <strong class="pick-value">{washer_verdict}</strong>
            <h2>Hold until delivered total is proven</h2>
            <p class="meta">Best supported saving {washer.get('price', '--')}. Public item-page pricing is not enough; compare delivered checkout terms before treating the pair as a buy.</p>
            <div class="sub-links">
              <a href="dashboards/washer.html">Savings trend</a>
              <a href="dashboards/washer.html">Decision gate</a>
              <a href="dashboards/washer.html">Checkout caution</a>
            </div>
          </div>
          <a class="button primary" href="dashboards/washer.html">Open public-safe view</a>
        </article>
        <article class="pick-card stroller-card">
          <div class="pick-media" aria-hidden="true"></div>
          <div>
            <div class="pick-top">
              <span class="pick-rank">3</span>
              <span class="pick-label">Nuna stroller price board</span>
            </div>
            <strong class="pick-value">{stroller_price} verified used lead</strong>
            <h2>Message seller before treating it as safe</h2>
            <p class="meta">The price is under target, but the infant seat requires complete crash, expiry, label, recall, and insert verification.</p>
            <div class="sub-links">
              <a href="dashboards/stroller.html#price-ladder">Price ladder</a>
              <a href="dashboards/stroller.html">Safe-buy options</a>
              <a href="dashboards/stroller.html">Safety checklist</a>
            </div>
          </div>
          <a class="button primary" href="dashboards/stroller.html">Open Julie price board</a>
        </article>
      </div>
    </div>
  </header>

  <main>
    <section class="section">
      <div class="wrap">
        <div class="section-head">
          <div>
            <p class="eyebrow">Public-safe views</p>
            <h2>Every tracker, one board</h2>
          </div>
          <p>Every link in this hub stays inside the Luke/Julie-safe repository. Recipient-specific dashboards have separate delivery and no runtime path from here.</p>
        </div>
        <div class="grid">
          <article class="card">
            <span class="status live">Active</span>
            <div>
              <h3>Ford Raptor Tracker</h3>
              <p class="meta">{ford.get('count', 0)} eligible leads, lowest {ford_price}. Price trend, band, and market coverage.</p>
            </div>
            <a class="button" href="dashboards/ford.html">Open public-safe view</a>
          </article>
          <article class="card">
            <span class="status hold">{washer_verdict}</span>
            <div>
              <h3>Washer Deal Tracker</h3>
              <p class="meta">Best supported saving {washer.get('price', '--')}. Detailed checkout evidence stays private.</p>
            </div>
            <a class="button" href="dashboards/washer.html">Open public-safe view</a>
          </article>
          <article class="card">
            <span class="status live">Active</span>
            <div>
              <h3>Baby Gear Tracker</h3>
              <p class="meta">{baby.get('purchased', 0)} of {baby.get('requested', 0)} registry items purchased. Budget and category snapshot.</p>
            </div>
            <a class="button" href="dashboards/baby.html">Open public-safe view</a>
          </article>
          <article class="card">
            <span class="status live">Active</span>
            <div>
              <h3>Nuna Stroller Tracker</h3>
              <p class="meta">Julie-focused price ladder, purchase-worthy leads, and car-seat safety guardrails.</p>
            </div>
            <a class="button primary" href="dashboards/stroller.html">Open Julie price board</a>
          </article>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="section-head">
          <div>
            <p class="eyebrow">Private lanes</p>
            <h2>Not published from this hub</h2>
          </div>
          <p>These stay private because the exact dashboards expose sensitive context. They are delivered as a rendered dashboard inside the email body instead, which needs no public URL.</p>
        </div>
        <table class="table panel">
          <thead>
            <tr><th>Dashboard</th><th>Status</th><th>Public-safe handling</th></tr>
          </thead>
          <tbody>
            <tr><td>Ford Raptor, full detail</td><td>Private active</td><td>Financing scenarios and per-listing source links are delivered in the email body only.</td></tr>
            <tr><td>Token Cost Tracker</td><td>Private active</td><td>Rendered in the email body. No public cost details.</td></tr>
            <tr><td>Jackson/Yellowstone Weather</td><td>Archived</td><td>No public link. Historical trip details stay private.</td></tr>
            <tr><td>NextDecade Dashboards</td><td>Archived</td><td>No public copy of exact skill-map or source-of-truth internals.</td></tr>
            <tr><td>Active Directory Dashboard</td><td>Archived</td><td>No public copy of AD model files, extracted report content, or company system detail.</td></tr>
            <tr><td>Work Intake Governor</td><td>Private</td><td>No public copy because reports can include local paths and sensitive filenames.</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="wrap">Main dashboard updated {today}. Confirm final price, seller, stock, taxes, fees, pickup, and delivery timing before buying.</div>
  </footer>
</body>
</html>
"""


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the committed files differ from a fresh render")
    args = ap.parse_args()

    ford_html, ford = build_ford()
    washer_html, washer = build_washer()
    baby_html, baby = build_baby()
    index_html = build_index(ford, washer, baby)

    targets = [
        (ROOT / "dashboards" / "ford.html", ford_html),
        (ROOT / "dashboards" / "washer.html", washer_html),
        (ROOT / "dashboards" / "baby.html", baby_html),
        (ROOT / "index.html", index_html),
    ]

    stale = []
    for path, html in targets:
        if html is None:
            print(f"  skipped {path.name} (no source data on this machine)")
            continue
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == html:
            print(f"  unchanged {path.name}")
            continue
        if args.check:
            stale.append(path.name)
            continue
        path.write_text(html, encoding="utf-8")
        print(f"  wrote {path.name} ({len(html)/1024:.1f} KB)")

    if args.check and stale:
        print(f"\nSTALE: {', '.join(stale)} do not match the current tracker data. "
              f"Run: python3 tools/publish_dashboards.py", file=sys.stderr)
        sys.exit(1)
    if args.check:
        print("\nAll public dashboards match the current tracker data.")


if __name__ == "__main__":
    main()
