# WP-012 — Interactive provisional family diagrams

Status: development candidate, not a released family-tree UI.

## Scope

- Authenticated `GET /api/v1/research/hypotheses/{set_uuid}/tree-view[?option_key=...]`.
- Deterministic, bounded coordinate layout of historical **record appearances** (not merged people).
- Solid lines for proposed parent links, dashed for other asserted relationships, distinct contradiction mark.
- Browser SVG generated through text-safe DOM APIs, a zoom control and accessible relationship detail list.
- Explicit empty diagram for the unknown-relative alternative.
- No schema migration, external network calls, Gramps tree writes, AI-supplied confidence or calibrated probability numbers.

## Caveats / next features

This is a provisional research visual, not the accepted Gramps tree, true family-unit grouping, verified pedigree fan chart, geospatial map or historical timeline. Multiple records for one person are deliberately NOT merged. Later modules must handle verified identity resolution before plotting individual-level pedigree structures.

The application is restricted to localhost, existing authentication and approved private research use; personal names must never be logged from diagrams.

## Acceptance

- Bounded deterministic diagrams, cycle refusal, structured family links, unknown option.
- Browser text rendering never uses `innerHTML` for historical-record content.
- `calibrated_probability=null` and `gramps_written=false` in every response.
- Tests passing on Windows Python 3.12; no automatic migrations or accepted-tree writes.
