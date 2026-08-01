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
title: "What I learnt building the PWR elasticity model"
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

### Option B — Redirect to a LinkedIn article (`type: linkedin`)

A lightweight stub that immediately redirects to an external URL. Appears under **On LinkedIn** on the homepage.

```yaml
---
layout: post
type: linkedin
title: "Accuracy matters, but usefulness matters more."
date: 2026-04-28
redirect_to: https://www.linkedin.com/pulse/...
---
```

Any post without a `type` field defaults to the LinkedIn sub-group.

## Adding a project card

Create a new file in `_projects/` — no changes to `index.html` needed.

```yaml
---
title: "Project title"
period: "May 2026"            # display string shown on the card (use 'period', not 'date')
context: "Hackathon · NHS"   # shown after period with · separator
github: "https://github.com/chaeyoonakim/your-repo"
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

## License

Code in this repository is released under the [MIT License](LICENSE).

All written content — blog posts, CV, project descriptions, and other prose —
is © 2026 Chaeyoon Kim, all rights reserved, and is not covered by the MIT
license.