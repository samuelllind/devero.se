# devero.se

The Devero studio site: the apps, FUT 27 Pack Opener's FAQ and privacy policy, and contact.
Plain HTML and one stylesheet, no build step, served by GitHub Pages on `devero.se`.

Design: `docs/superpowers/specs/2026-10-17-devero-site-design.md` in the FUT 27 repo.

## Rules

- Say "Devero", never "Devero AB": Devero is not a registered company.
- No third-party requests (scripts, styles, fonts, analytics). The privacy policy says so.
- Every page fits a 320 px wide phone and works without JavaScript.
- Pages are folders with `index.html`; link to them with a trailing slash (`/fut27/`).
- The header and footer are copied into each page; change them everywhere at once.

## Checks

```bash
npm ci && npx playwright install chromium   # once
npm test                                    # unit tests for the site check
npm run check                               # links, rules, and the 320 px layout
python3 -m http.server                      # preview at http://localhost:8000
```

Barlow Condensed is under the SIL Open Font License (`assets/fonts/OFL.txt`).
