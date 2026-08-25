# Multi-source PPTX starter adapter

This package assembles explicitly selected native slides from two or more PPTX
sources into `template-starter.pptx`. It is a narrow starter builder, not a full
presentation authoring or visual-review engine.

## Requirements

- Node.js 20 or newer;
- npm with the committed `package-lock.json`;
- source deck paths relative to `--project-root`.

Install and verify in a clean directory:

```bash
npm ci
npm run verify
```

Run the adapter:

```bash
node build_multisource_starter.mjs \
  --plan plan.json \
  --project-root ./fixture-project \
  --out ./output/template-starter.pptx \
  --receipt ./output/receipt.json
```

The adapter fails closed when the output or receipt already exists, an input
deck path is absolute or escapes the project root, an internal OOXML
relationship is broken, an unreferenced package part remains, or a local
filesystem path is embedded in the final PPTX.

Before `pptx-automizer` runs, every source deck is reduced to the explicitly
selected slides. Unselected slide, notes, media, layout and master parts are
removed from the temporary source copy. The public starter also strips all
speaker notes and comments, including those attached to selected slides.

Temporary sanitized source copies are created under the operating system's
temporary directory and removed before the process exits. They are never
listed with absolute paths in the receipt.

## Independent package QA

```bash
node verify_pptx_package.mjs \
  --pptx ./output/template-starter.pptx \
  --expected-slides 2
```

The verifier checks the visible slide count, internal relationships,
unreferenced OOXML parts and local-path traces. A passing package-safety report
does not claim visual fidelity, formal editing completion or business approval.

## Dependency security boundary

`pptx-automizer` is pinned to `0.9.3`. Its transitive `pptxgenjs` dependency
currently retains an `image-size` version covered by upstream denial-of-service
advisories for ICNS, JXL and HEIF images, and upstream lists no patched
`image-size` release. This adapter therefore rejects ICNS, JXL, HEIF, HEIC and
AVIF media by both extension and file signature before Automizer receives the
deck. Regression tests cover disguised ICNS, JXL and HEIF payloads.

See `SECURITY.md` for the exact limitation. A non-zero `npm audit` result for
these recorded advisories must not be reported as an audit pass.
