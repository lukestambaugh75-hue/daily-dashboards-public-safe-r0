# Warm baby + stroller dashboard implementation plan

## Goal

Redesign the combined public-safe Baby + Stroller dashboard as a calm, warm, Apple-inspired decision surface. Keep the best verified new stroller price visible in the opening view, provide a clear top-level Stroller/Baby gear switch, and preserve public-safe audience boundaries and safety-gated stroller language.

## Implementation sequence

1. Add failing generated-page contract tests for the warm hero, two decision metrics, semantic segmented control, “Worth looking at” decision rows, and removal of the old cycle-only interaction.
2. Replace the combined page’s dense dark treatment with scoped warm markup and CSS in the source generator. Keep the existing dashboard generators unchanged and retain detailed stroller and baby content below the decision layer.
3. Regenerate the public artifacts and run the focused tests, full public test suite, link verifier, and audience/privacy checks.
4. Inspect the live page at desktop and mobile widths with screenshot evidence. Exercise the Stroller/Baby gear switch and keyboard focus state.
5. Score the result across ten UX criteria (10 points each): decision clarity, hierarchy, warm visual language, stroller usability, baby discoverability, responsive behavior, accessibility, data honesty, action clarity, and visual restraint. Iterate any score below 9 or any P0/P1 issue. Accept only at 90/100 or better.
6. Record the final red-team score and evidence in `docs/audits/2026-07-12-warm-dashboard/UX-RED-TEAM.md`, then commit and push the verified public artifacts.

## Acceptance criteria

- One public URL contains both detail layers and no private or Devin-specific links.
- Best new stroller price remains above the fold.
- Stroller and Baby gear are two clearly labeled, keyboard-accessible states.
- The default state makes the safe new fallback and verify-first lead understandable without opening a dense table.
- The layout works at 1440px and 390px widths without horizontal scrolling.
- Automated tests and the screenshot red-team score pass.
