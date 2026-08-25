# Residential Competitiveness Public Core — v0.1.0-rc.1

This is the public release candidate for a platform-neutral residential-project
competitiveness production core. Anyone can clone, download, inspect and run it without
repository access approval.

The first complete fictional-project flow passes in a standard Python and Node runtime.
Start with [`START_HERE.md`](START_HERE.md); this README records the package boundary.

The repository is licensed under [Apache License 2.0](LICENSE). Public RC status and
support boundaries are recorded in [`RELEASE_STATUS.md`](RELEASE_STATUS.md).

## Included runnable capabilities

- Chinese assertion-style copy linting;
- Product 3 chapter 2 and chapter 3 contract validation;
- Product 3 chapter 2-to-3 bridge validation;
- Product 4 contract and XMind validation;
- Generic Product 3 business gates;
- synthetic Markdown security fixtures;
- a narrow multi-source native-slide PPTX starter adapter with OOXML package QA.

## Python verification

The Python core uses only the standard library.

```bash
python3 tests/run_public_tests.py
```

## Complete fictional cold start

```bash
python3 scripts/run_rc1_demo.py --install-node-deps
```

The command produces a local receipt under `verification-tmp/fictional-demo/`. The
confirmed state is `local_fictional_e2e_pass`: method contracts, platform round-trip,
PPTX structure and the Product 5 static bundle pass. Formal visual review, independent
machine use and WorkBuddy adaptation remain separate validation states.

This local command is a reference implementation, not the external portability test.
The fixed-tag, zero-content-guidance WorkBuddy procedure is defined in
[`COLD_START_PROTOCOL.md`](COLD_START_PROTOCOL.md).

## PPTX starter verification

The PPTX adapter requires Node.js 20 or newer and standard npm dependencies.

```bash
cd tools/product3_ppt_pipeline/automizer_adapter
npm ci
npm run verify
```

The adapter retains only explicitly selected source slides, strips notes and
comments, removes unreachable OOXML parts, rejects absolute source paths, and
writes a path-portable receipt. Its independent verifier checks slide count,
relationships, orphan parts and embedded local-path traces.

This is structural package QA, not a presentation renderer. Formal slide design,
high-fidelity generation and rendering belong to the selected platform adapter
(for example Codex, WorkBuddy, another agent platform or a human production team).
They are not public-core implementation requirements. The transitive
`image-size` security advisories and their compensating input control are
recorded as a time-bounded dependency exception; `npm audit` is not reported as
passing.

## v0.1 convergence target

The public candidate proves that a user with no private project history and no Codex
runtime can execute one fictional residential-project flow in a clean standard runtime:

`START_HERE → research contracts → fictional evidence → Product 3 production input
→ platform-generated presentation → public QA → Product 5 generic shell → static
bundle → delivery checks`.

Only components required to close that flow enter RC1. Independent WorkBuddy cold start
is the next portability validation, not a download or installation gate. See
`V0_1_RELEASE_SCOPE.md`.

## Deliberately excluded

- all real projects, customer materials, production assets and private evaluation data;
- private Git history, branches, tags and repository metadata;
- local machine paths, credentials, internal domains, SSH profiles and hosting state;
- platform-specific presentation, hosting and high-state production runtimes;
- components that are not required by the RC1 fictional end-to-end flow;
- formal PPT generation engines, Grist, cloud publishing profiles and real project
  Product 5 implementations;
- A4 PDF generation unless the RC1 flow later proves it is needed.

See `PUBLIC_CORE_MANIFEST.json`, `RELEASE_MANIFEST.json`, `A_CLASS_ALLOWLIST.txt`,
`B_CLASS_PROMOTION_MANIFEST.json`, `V0_1_RELEASE_SCOPE.md` and
`DEPENDENCY_EXCEPTIONS.json` for the exact candidate boundary. Third-party license and
security boundaries are recorded in `THIRD_PARTY_NOTICES.md`,
`THIRD_PARTY_LICENSES.json` and `SECURITY.md`.
