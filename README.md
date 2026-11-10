# News Bites v0.6 — Editorial filtering preview

This is a free, source-linked RSS prototype, **not** a fact-checked or AI-summarized publication. Headlines and descriptions come from RSS publishers. The story ranking is heuristic, and the original source remains the place to verify any claim.

## What's new
- Approximate event-level deduplication: merges some overlapping headlines, but may miss paraphrases or occasionally merge distinct developments.
- Explicit, explainable scoring from headline keywords, recency, and independent feed corroboration. This is a **prototype heuristic**, not a guarantee that the Top 3 are the most important stories worldwide.
- Category keyword classification and per-source/per-category caps. Categories may be imperfect.
- 4 PM update does **not** overwrite the morning Top 3: only adds up to three new, higher-scoring source-linked developments, if any.
- Keeps the last generated edition if fewer than three morning items can be retrieved.
- Maintains the approved dark seafoam visual design and browser text-to-speech.

## Updating your existing GitHub repository

Replace these **three files** with the matching files from this ZIP, preserving the exact paths:

1. `scripts/build.py`
2. `.github/workflows/news.yml`
3. `README.md`

You do not need to replace `index.html` or `template.html` for this upgrade; the existing `template.html` is compatible. The ZIP includes them for complete fresh installations. If you want the easiest installation, upload all root-level files and recreate the nested files through GitHub's editor as before.

After updating, go to **Actions → News Bites updates → Run workflow**, choose **morning**, and run it. Wait for the green checkmark, then refresh GitHub Pages. The scheduled 4 PM run uses the afternoon mode. GitHub scheduled jobs can be late or skipped; the 6 AM and 4 PM targets are not guaranteed.

## Cost, licensing, and limitations
- Python standard library only. No AI API, paid hosting, paid database, or payment method required.
- A free GitHub Pages site on a public repo is the intended host, subject to provider limits and policies.
- RSS feed availability and redistribution rights vary; do not treat descriptions as licensed for unrestricted republication.
- No evidence-backed "Why it matters" or researched Read More yet. We deliberately do not fabricate them.
- No real-time notifications, push alerts, independent fact checking, or verified timeline.
- The 4 PM run detects new qualifying **headlines**, not reliably new developments in an existing story.
- `edition.json` is generated automatically and should not be edited manually.

## Local test

`python scripts/build.py` runs a morning collection. For an afternoon check: `NEWS_BITES_MODE=afternoon python scripts/build.py` (on Windows PowerShell, set `$env:NEWS_BITES_MODE='afternoon'` first).
