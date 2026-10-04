# Data, ethics, and lessons learned

Chaeyoon Kim — Data Scientist based in London.

Jekyll site and writing blog covering data science practice, AI ethics, and lessons from real-world health-data projects.

## Structure

```
_layouts/
  default.html   # site shell, all CSS, nav, footer
  post.html      # writing page: renders full content or redirects to an external URL
_posts/          # all writing entries (Markdown) — both on-site posts and redirect stubs
_projects/       # project cards (Markdown front matter only, output: false)
assets/
  img/           # static images (e.g. project poster thumbnails)
index.html       # homepage — hero · about · projects · writing
cv.html          # standalone CV page at /cv
scripts/
  build_cv.py    # regenerates assets/Chaeyoon_Kim_CV.pdf (not published)
_config.yml      # site metadata (title, url, plugins, collections)
Gemfile          # Jekyll 4.3 + jekyll-feed, used by CI
```

## Pages

| Route | File | Description |
|-------|------|-------------|
| `/` | `index.html` | Hero, About (with CV link), Projects, Writing |
| `/cv` | `cv.html` | Full CV — experience, education, community |
| `/:year/:month/:day/:title/` | `_posts/*.md` | Individual writing entries |

## Writing

Everything goes in `_posts/` as `YYYY-MM-DD-your-title.md`. The `type` field controls which sub-group the card appears in on the homepage, and whether the page renders on-site or redirects.

### Option A — Write your own post on-site (`type: reflection`)

Full Markdown content rendered on the site. Appears under **Reflections & project notes** on the homepage. Inspired by the [NHS England our_work](https://github.com/nhsengland/datascience/tree/main/docs/our_work) format.

```yaml
---
layout: post
type: reflection
title: "What I learnt building the NHS Policy Navigator"
date: 2026-05-25
summary: "One-line description shown on the homepage card."
tags: [econometrics, NHS, panel-data]
---

## Background

## What I did

## Lessons learnt

## Outputs
```

- `summary` — shown as the card excerpt on the homepage (optional; falls back to post excerpt)
- `tags` — displayed as pills on the card and the post page (optional)

### Option B — Redirect to an external article or talk (any `type` other than `reflection`)

A lightweight stub that immediately redirects to an external URL. Appears under **Talks & articles** on the writing page.

```yaml
---
layout: post
type: linkedin
title: "Accuracy matters, but usefulness matters more."
date: 2026-04-28
redirect_to: https://www.linkedin.com/pulse/...
---
```

- `type` — any value other than `reflection` groups the post here; use something descriptive (`linkedin`, `external`, `talk`, …). A post without a `type` field also defaults to this group.
- `redirect_note` — optional; the sentence shown above the button (defaults to "This article is published on LinkedIn Pulse.")
- `redirect_label` — optional; the button text (defaults to "Read on LinkedIn ↗")

For a non-LinkedIn redirect (e.g. a conference poster page), set `redirect_note`/`redirect_label` to match:

```yaml
---
layout: post
type: external
title: "Vibe coding for England Pharmacy analysis with open data"
date: 2025-12-03
redirect_to: https://nat-stephenson.github.io/HACA_Quarto_Book/theme3.html
redirect_note: "This poster was presented at the Health and Care Analytics (HACA) Conference 2025."
redirect_label: "View poster ↗"
---
```

## Adding a project card

Create a new file in `_projects/` — no changes to `index.html` needed.

```yaml
---
title: "Project title"
period: "May 2026"            # display string shown on the card (use 'period', not 'date')
context: "Hackathon · NHS"   # shown after period with · separator
github: "https://github.com/chaeyoonakim/your-repo"
url: "https://your-app.example.com/"  # optional — live app; card opens it and shows a "Source code" pill for the repo
badge: "In Progress"         # optional pill label (e.g. "1st Place", "In Progress")
featured: true               # optional — spans full grid width, shows thumbnail
thumb: "/assets/img/your-thumbnail.jpg"  # local path or absolute https:// URL
thumb_alt: "Alt text for thumbnail"      # optional
excerpt: "One-paragraph description shown on the card."
order: 6                     # controls display order (lower = first)
---
```

**Notes:**
- Use `period` not `date` — Jekyll tries to parse `date` as a Ruby date object.
- `thumb` accepts a local path or an absolute URL. Pin external images to a commit SHA for stability.
- CI validates every `thumb` value on each PR: external URLs via `curl --location`, local paths against built `_site/`.

## Updating the CV

The CV lives in two places: `cv.html` (the `/cv` page) and the downloadable
`assets/Chaeyoon_Kim_CV.pdf`. Edit the text in both `cv.html` and
`scripts/build_cv.py`, then regenerate the PDF:

```bash
pip install reportlab
python scripts/build_cv.py
```

## License

Code in this repository is released under the [MIT License](LICENSE).

All written content — blog posts, CV, project descriptions, and other prose —
is © 2026 Chaeyoon Kim, all rights reserved, and is not covered by the MIT
license.