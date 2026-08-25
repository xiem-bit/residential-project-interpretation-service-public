# Security boundary

This adapter is a local batch tool for assembling explicitly selected slides.
It is not designed as a network service and does not make untrusted PPTX input
safe for arbitrary downstream software.

## Recorded upstream advisories

As of 2026-08-25, `pptxgenjs@3.12.0` depends on an `image-size` release covered
by these GitHub-reviewed denial-of-service advisories:

- `GHSA-w3rx-r6r6-pgpr`: malformed ICNS input;
- `GHSA-5p2g-fcmc-qvqq`: malformed JXL or HEIF input.

The advisory database lists no patched `image-size` release. The adapter blocks
the affected format families before `pptx-automizer` runs:

- denied extensions: `.avif`, `.heic`, `.heif`, `.icns`, `.jxl`;
- denied signatures: ICNS, JPEG XL codestream/container, and HEIF-family brands;
- failure occurs before the output PPTX or receipt is created;
- synthetic disguised-media regression tests must pass in `npm run verify`.

This is a compensating control, not a claim that the transitive dependency has
been patched. Re-evaluate and remove the exception when an upstream fixed
release becomes available. Continue to use trusted source decks and run the
tool with ordinary user privileges.
