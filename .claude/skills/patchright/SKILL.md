---
name: patchright
description: >
  Extract data from websites that have no public API by driving a stealth
  Chromium (Patchright, an undetected drop-in replacement for Playwright) and
  listening to the site's own network requests (XHR / fetch / GraphQL JSON).
  Use when a page loads its data dynamically, when Scrapling's parser only sees
  an empty shell, or when the cleanest source of truth is the JSON the site's
  frontend already fetches. Workflow: user says what data they need → write the
  script → collect → return structured results.
metadata:
  homepage: https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python
  inspired_by: https://github.com/whaleyxbt/patchright-enhanced
---

# Patchright — capture the API a site uses internally

Patchright is Playwright with stealth patches (no `Runtime.enable` leak,
`navigator.webdriver` false, no `--enable-automation`). Same API as Playwright:
`from patchright.sync_api import sync_playwright`.

## When to pick which tool

| Situation | Tool |
|---|---|
| Social platforms (X, Reddit, YouTube, GitHub…) | `agent-reach` skill first |
| Static HTML / anti-bot page / crawling many pages | `scrapling` skill |
| Data loaded by JS from an internal API, no public API | **this skill** |

## Workflow

1. **Discover**: open the page once and log every JSON response
   (URL, status, first 300 chars). Scroll / click to trigger lazy loading.
2. **Pick** the endpoint(s) that carry the data.
3. **Collect**: filter responses on that URL pattern, parse JSON, paginate by
   scrolling or by replaying the request with `page.request.get(...)`
   (inherits cookies/headers of the browser context).
4. **Output**: write results to `/tmp/<task>/…json|csv`, then summarise for the user.

## Template

```python
import json, re
from patchright.sync_api import sync_playwright

TARGET = "https://example.com/page"
PATTERN = re.compile(r"/api/|graphql")  # adjust after discovery
captured = []

def on_response(resp):
    if PATTERN.search(resp.url) and "json" in resp.headers.get("content-type", ""):
        try:
            captured.append({"url": resp.url, "data": resp.json()})
        except Exception:
            pass

with sync_playwright() as p:
    # Cloud sessions: Chromium is pre-installed; locally prefer channel="chrome".
    browser = p.chromium.launch(
        headless=True,
        executable_path="/opt/pw-browsers/chromium",
    )
    ctx = browser.new_context(locale="fr-FR")
    page = ctx.new_page()
    page.on("response", on_response)
    page.goto(TARGET, wait_until="networkidle")
    for _ in range(5):  # trigger infinite scroll / lazy loading
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(1500)
    browser.close()

json.dump(captured, open("/tmp/patchright_capture.json", "w"), ensure_ascii=False, indent=2)
print(len(captured), "responses captured")
```

If `executable_path` doesn't exist, drop it and run `patchright install chromium` first.

## Rules

- Output files go in `/tmp/`, never in the repo.
- Stay polite: small delays between actions, no parallel hammering, stop on
  429/403 instead of looping. Respect the site's terms and personal data rules (RGPD).
- Read-only: never post, like, log in with someone else's account or submit forms
  unless the user explicitly asks.
