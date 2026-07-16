# gh-16027: `st.expander` content permanently clipped after interrupted open/close animation

## Summary

After certain *rapid* open/close sequences across several `st.expander`s on a
long, chart-heavy page, one expander can end up permanently clipped: it renders
at a stale fixed height with the tail of its content cut off and unreachable
until a rerun/reload. The root cause is a real, confirmable gap in the frontend
open/close animation cleanup — a cancelled height animation leaves an inline
`height`/`overflow: hidden` lock on the `<details>`, and there are paths where
no follow-up animation ever clears it.

## Finding

**Bug confirmed at the code level; behavior is a non-deterministic timing race
that could not be triggered by automated Playwright.** The reporter's root-cause
analysis was verified line-by-line against the source on `develop` (identical to
1.59.2). The race itself did not reproduce in 200+ automated rapid-toggle bursts
on the reported version, including runs with 6× CPU throttling — consistent with
the reporter's own note that it "may take a few attempts" and is likeliest on a
heavy, slow-to-lay-out page. Verdict: **needs_human_review**.

## Reproduction

- **Version tested:** 1.59.2 (released wheel, throwaway `uv` venv), served on
  `localhost:8602`; served version confirmed `1.59.2`.
- **Method:** self-contained Playwright script (`verify_gh_16027.py`) driving the
  reporter's sequence — expand the collapsed bottom expanders, collapse the open
  top ones, then rapidly collapse + re-expand the bottom ones — across all 7 real
  expanders, with sub-animation gaps so animations are cancelled mid-flight.
- **Detection:** after each burst, wait past the 500 ms animation + 10 ms
  ResizeObserver debounce, then inspect each `div[data-testid="stExpander"] >
  details` for the stale-lock signature: `open` + inline `overflow: hidden` +
  inline `height` + **no running WAAPI animation** + content clipped
  (`scrollHeight - clientHeight > 5`).
- **Result:** 0 stale-locks across 80 plain bursts and 120 chaotic, randomly
  timed bursts under 6× CPU throttling. Every expander settled cleanly
  (`inlineHeight=""`, `inlineOverflow=""`, `clipped=false`). Screenshot:
  `settled.png`.
- **Note (avoided a known trap):** port 8600 held an orphaned server from
  another agent; this run used a fresh 1.59.2 server on 8602 and verified the
  served version before testing.

The gap in automated reproduction is a limitation of headless timing, **not**
evidence the bug is absent — the defect is present in the code (below).

## Root Cause

The animated `<details>` open/close/resize is driven by
`frontend/lib/src/components/elements/Expander/useDetailsAnimation.ts`, which
locks the element before every animation and relies on the animation's **finish**
event to unlock it:

- `animateHeight()` (`animateHeight.ts:65-88`) clears the inline styles **only**
  on `finish`:
  ```ts
  animation.addEventListener("finish", () => {
    element.style.height = ""
    element.style.overflow = ""
    onFinish?.()
    resolve()
  })
  animation.addEventListener("cancel", () => {
    // DON'T clean up on cancel - caller will set new styles
    resolve()
  })
  ```
  The `cancel` branch deliberately leaves `height`/`overflow` in place, on the
  invariant that the caller always re-locks and starts a follow-up animation that
  will eventually `finish`.

- `animateTo()` / `animateResize()` (`useDetailsAnimation.ts:161-164`, `:221-224`)
  do lock synchronously right after `cancelAnimation()`, so the common path is
  safe. But that invariant breaks in at least these paths, leaving the element
  locked with **nothing running to clear it**:
  1. **Open path with `contentHeight === 0`** (`useDetailsAnimation.ts:176-191`):
     cancels, sets `height`/`overflow`, opens, measures content as 0, and then
     *deliberately schedules no animation*, relying on the ResizeObserver to heal
     it later.
  2. **ResizeObserver early-returns** (`useDetailsAnimation.ts:236-266`): the
     debounced healer bails on `!details.open`, `!isOpenRef.current`, or a height
     delta below `RESIZE_THRESHOLD_PX` (5 px) — so the promised follow-up
     animation may never run.
  3. **Unmount cleanup** (`useDetailsAnimation.ts:346-351`) calls
     `cancelAnimation()` without clearing styles (harmless because the node is
     discarded, but part of the same pattern).

  A rapid toggle chain across several expanders (each toggle calls
  `cancelAnimation()` first) can therefore end on a cancel whose "successor" hits
  one of these early-returns, leaving `<details>` at a stale locked height with
  `overflow: hidden` → content clipped and unreachable.

`StyledDetails` in `styled-components.ts` sets no `height`/`overflow` of its own,
so any inline `overflow: hidden` observed at rest is residue from this cleanup
gap. The "new expander" path (`useDetailsAnimation.ts:281-293`) explicitly clears
these inline styles, which is why a rerun/reload heals the state.

**Code pointers:**
- `frontend/lib/src/components/elements/Expander/animateHeight.ts:78-82` (cancel
  listener does not clear styles)
- `frontend/lib/src/components/elements/Expander/useDetailsAnimation.ts:176-191`
  (open path leaves lock when `contentHeight === 0`)
- `frontend/lib/src/components/elements/Expander/useDetailsAnimation.ts:236-266`
  (ResizeObserver healer early-returns)

**Regression origin:** the animated-expander logic (this cancel-without-cleanup
pattern) was introduced in **1.55.0** — `#13933` "extract Expander animation
logic into useDetailsAnimation hook" and `#13934` "improve Expander animation
with ResizeObserver, smooth interruption, and nullable expanded handling"
(commits `67ac679ed4` / `6f993c6aa3`, 2026-02-13/14). Expanders animated open/
close was not present before that, matching the reporter's "used to work in a
previous version."

## Suggested fix (from reporter, verified as sound)

Clear the inline `height`/`overflow` in the `cancel` listener (or inside
`cancelAnimation()`), and let the follow-up animation re-lock — callers already
re-lock synchronously right after cancelling, so clearing on cancel is safe and
makes "locked with nothing running" an unreachable state. This is a small,
low-risk change localized to `animateHeight.ts` / `useDetailsAnimation.ts`.

## Classification

- **Type:** Bug — regression
- **Status:** Root cause confirmed on 1.59.2 (code); race not reproduced by
  automated Playwright (needs human review)
- **Areas:** frontend, `Expander` (`useDetailsAnimation` / `animateHeight`)
- **Priority:** **P2 (low end, borderline P3)** — It's a regression (introduced
  1.55.0) with a straightforward, low-risk known fix, which per
  `wiki/issue-prioritization.md` argues for fixing in an upcoming release (P2).
  But reach measured by the *broken behavior* is very narrow: it only triggers on
  a power-user rapid-toggle pattern on a heavy page (undetectable in 200+
  automated attempts) and self-heals on any rerun/reload, so a typical user
  toggling expanders normally never notices. That narrowness and difficulty of
  reproduction is what keeps it at the bottom of P2 rather than higher, and a
  reasonable case exists for P3 given the "very specific situations, difficult to
  reproduce" descriptor. Calibrated against #16003 (P2, narrow-but-default-path
  regression); this is narrower and self-healing, but the symptom (content
  becoming unreachable) is more severe when hit.
- **Fix complexity:** Small — clear inline styles on cancel; add a regression
  test for the cancel-with-no-successor path.
