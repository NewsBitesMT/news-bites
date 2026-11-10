# News Bites — live RSS preview v0.5

This is a **free, source-linked headline preview**, not the finished editorial news digest. It deliberately does **not** invent summaries, “Why it matters” claims, or long-form explanations. Publisher RSS descriptions are labelled as such.

## Get it running at €0

1. Create a **public** GitHub repository (free) and upload all the files in this folder, including `.github/workflows/news.yml`.
2. In the repository's **Actions** tab, open **News Bites updates** and select **Run workflow**. The workflow fetches feeds and commits `index.html` and `edition.json` when at least three suitable articles are found.
3. In **Settings → Pages**, choose **Deploy from a branch**, branch `main` (or your default branch), folder `/ (root)`; save. The site appears on a free `github.io` address.
4. Open the URL on your phone. Bookmark it or add it to your home screen. This version is **not yet an offline-installable PWA**.

The scheduled jobs target **05:55 and 16:00 Europe/Malta**. GitHub may delay or drop scheduled runs, so neither publication at exactly 06:00 nor the 16:00 check is guaranteed. The 16:00 run refreshes the same source preview; it is **not yet a separate significance-filtered breaking-news alert**.

## Limits and safeguards

- No API keys, payment details, third-party AI, or paid services.
- Uses publisher RSS titles and descriptions, links and timestamps. RSS feed availability and permitted uses must be checked before broader distribution.
- The selection logic is a basic recent-headline preview, **not a verified importance ranking**. Top 3 means three selected recent items, not necessarily the world's most consequential stories.
- Up to 12 items from supported feeds, maximum 3 from Times of Malta if available. Category assignments are provisional.
- RSS descriptions may be incomplete or contain publisher wording. News Bites labels them as publisher-provided and does not claim independent verification.
- The Times of Malta feed may be empty or unavailable; the workflow skips unavailable feeds.
- If fewer than 3 fresh items are available, the build fails and the previously published `index.html` stays in place.
- The Story So Far section remains a **labelled illustrative timeline**, not a live report.
- A public GitHub repo and Pages are free under current free-plan conditions; terms and quotas may change. No guarantees of indefinite zero cost.
- Some RSS feed providers may restrict republication of descriptions. Check permissions before sharing broadly; source-linked titles alone are a safer fallback.

## Test locally

`python scripts/build.py` (Python 3.9+ with timezone database; 3.12 recommended). Internet access required.

## Next development tasks

1. Validate feeds and permissions, add Malta-specific trusted sources.
2. Improve deduplication and consequence-based ranking, and distinguish the 4 PM update from the morning edition.
3. Add evidence-grounded, original summaries and “Why it matters” only when defensible with free processing.
4. Replace the sample timeline with sourced dated developments.
5. Add proper installable PWA assets and robust publication/alert logs.
