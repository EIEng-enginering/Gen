# WP-009: Provenance-linked historical places and English record candidate triage

Status: DEVELOPMENT CANDIDATE. **No calibrated match probabilities, AI scraping or Gramps writes.**

## Delivered

- Migration `20261023_005` after revision `20261023_004`: new `historical_places` with document FK, immutable source/key identifier, labels, old county, kind, validity years, text aliases and evidence note; downgrade refuses deletion with data.
- Authenticated `POST /api/v1/research/historical-places` (requires `X-24Gen-Intent: research`) and `GET /api/v1/research/historical-places` (bounded query, optional year).
- Authenticated read-only `GET /api/v1/research/observations/{id}/historical-candidates` uses bounded indexed surname-prefix retrieval and explainable heuristic ranking. Supports a *small curated list* of English given-name abbreviations and 1841 census adult-age rounding. All returned `calibrated_probability` values are null.
- Browser panel for entering/searching source-cited place references and comparing historical candidate rankings.
- Unit/API tests and upgrade+data-preserving downgrade-refusal tests.

## Limitations / warnings

* The `historical_places` table is **not** an authoritative loaded gazetteer and does not reconstruct historic boundaries or calculate distances. Records require user-cited provenance; place aliases are stored for future source-aware matching.
* Surname two-character blocking cannot find every variant, and a 500-row retrieval cap may truncate common surnames. The API explicitly reports when retrieval may be incomplete.
* Only a recorded, numerically valid census age supplies a derived birth-year interval. A census event year is never treated as a birth year.
* Different event types can describe the same person decades apart, so event-year gaps do not prove false matches. This API is a suggestion tool, not identity-resolution proof.
* Numerical rankings cannot be shown as probabilities; population-level bias, independence of evidence, source provenance and posterior calibration remain future work.
* Source access restrictions still apply; this package does not download genealogy websites or perform LLM cloud requests.

Sources: https://www.nationalarchives.gov.uk/help-with-your-research/research-guides/census-records/ ; https://www.grampsweb.org/user-guide/data-model/
