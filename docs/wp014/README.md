# WP-014 — Historical Document and Evidence Comparison

**Status: developed locally; not live accepted.** This work package creates source-preserving dossier and comparison views. It introduces no database migration or external source fetch.

## Implemented

- `GET /api/v1/research/evidence/observations/{observation_id}/dossier`: source citation and licence, literal historical fields, original reading, bounded append-only transcription revision list and true latest reading.
- `POST /api/v1/research/evidence/compare`: 2–6 distinct registered observations, cited side-by-side comparison, literal field differences without inference, and WP-010 possible-shared-original groups.
- `GET /api/v1/research/evidence/capabilities`: truthful enforcement flags.
- `/workspace` **Evidence comparison**: accessible text evidence, citation cards, revision history, and local-only image preview supporting PNG/JPEG/WebP up to 20 MB and 25–300% zoom. Browser File/Blob object URLs are revoked when replaced or the page is left.

## Safety and data contract

No image bytes go to the 24 Gen server. The file input, blob and preview are temporary in the browser, not stored with a citation. The source catalogue references are always displayed; original images must be obtained lawfully by the researcher from permitted sources. All data rendering uses DOM `textContent`, not `innerHTML`. Reported literal differences do not imply two records concern the same individual. Separate source groups are not claimed independent. Original records and revisions remain immutable. No changes to Gramps accepted trees.

## Still missing before full R0.5 document viewer

Persistent rights-aware scanned-image import, checksum matching and media lifecycle, record-line bounding boxes, human HTR/OCR correction workflow, magnifier/image alignment, keyboard/browser test evidence and real Gramps media integration. A live synthetic-data browser check is mandatory.

## Tests

`tests/test_wp014_evidence.py`: authentication, conflicting source readings, latest correction preservation, no unknown or duplicate observations, manual common-original grouping and viewer safety flags.
