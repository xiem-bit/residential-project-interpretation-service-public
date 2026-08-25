# Third-party notices

The public-core Python tools use only the Python standard library. The optional PPTX
adapter installs JavaScript dependencies from the locked npm dependency graph under
`tools/product3_ppt_pipeline/automizer_adapter/package-lock.json`.

## Direct JavaScript dependencies

| Package | Locked version | Declared license | Use |
| --- | ---: | --- | --- |
| `jszip` | 3.10.1 | MIT OR GPL-3.0-or-later | OOXML ZIP inspection and cleanup |
| `pptx-automizer` | 0.9.3 | MIT | Selected native-slide assembly |
| `pptxgenjs` | 3.12.0 | MIT | Development/test adapter only |

The complete lockfile-derived inventory is stored in `THIRD_PARTY_LICENSES.json` and is
verified by `scripts/generate_third_party_inventory.py --check`. Dependencies are not
vendored into this repository; users install them with `npm ci`. Their own license and
notice files remain authoritative.

`jszip` is consumed under its MIT option. Its alternative GPL option does not change the
intended license of this repository. The time-bounded `image-size` security exception is
documented separately in `DEPENDENCY_EXCEPTIONS.json` and does not constitute a claim
that the upstream package is patched. At RC assembly time, `npm audit` reports three
high-severity affected package entries (`image-size`, `pptxgenjs` and `pptx-automizer`),
all tracing to the two recorded `image-size` denial-of-service advisories. The audit is
intentionally recorded as nonzero; no automatic dependency rewrite is applied.

This inventory accompanies the Apache-2.0 public RC. Third-party packages remain under
their respective licenses; the repository license does not replace those terms.
