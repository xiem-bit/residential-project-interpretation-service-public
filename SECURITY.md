# Security policy for the public core

This repository is a downloadable public release candidate, not a hosted service. Do
not place real customer documents, credentials or private project assets in public
issues, forks or reproducible test cases.

## Supported security checks

- source and generated-output scans reject owner-specific absolute paths and common
  credential signatures;
- PPTX package QA rejects broken relationships, unreachable OOXML parts and local-path
  traces;
- the static Product 5 bundle rejects symlinks, external resources and file-set changes;
- the recorded `image-size` advisories are controlled by denied media extensions and
  signatures, with a scheduled review in `DEPENDENCY_EXCEPTIONS.json`.

Security-sensitive findings should be reported through the repository's private
security-advisory channel. Do not place secrets, customer facts or exploit material in
ordinary issue comments.

The candidate must stop if an advisory expands beyond the recorded input families, a mitigation
test fails, the adapter becomes a network service, or public/uncontrolled uploads enter
its input boundary.

The v0.2 production core uses the Python standard library. Node dependencies belong to
the historical RC1 PPTX carrier adapter and are not required to discover or validate the
residential business strategy. Hidden-answer inputs, reference answers and review evidence
must remain outside the public repository until a sanitized observation record is approved.
