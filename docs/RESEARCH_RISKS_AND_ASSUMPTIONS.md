# Risk, Assumption and Decision-Control Register

| Risk | Impact | Mitigation and gate | Responsible stage |
| --- | --- | --- | --- |
| Git repo is private/inaccessible | No direct inspection or commit | Verify membership and exact owner/name before changes | WP-000 |
| OneDrive sync of live DB | Corruption/conflicts during active updates | Docker named volumes and active checkout outside OneDrive | WP-001 |
| Restricted source scraping | Licence and reputational risk | Per-source permission registry; manual links for restricted provider | WP-007 |
| False common-name identity match | Incorrect multi-generation ancestry | Calibrated historical pairwise model + family graph + review | WP-004/005 |
| Correlated transcriptions | Inflated confidence | Origin-group dependency graph and diagnostics | WP-002/004/005 |
| AI fabricated citation | Incorrect evidence claims | Structured output, cite-ID resolution, refusal on missing evidence | WP-004/015 |
| Missing/closed census records | Apparent lineage gap | Explicit unknown alternatives and source coverage indicators | WP-004/005 |
| Public exposure of local Basic auth | Credentials leaked | Localhost only; full security redesign before public hosting | WP-001 / future |
| Unrecoverable data or media | Permanent family-history loss | Cold backups, hashed manifests and isolated full restore drill | WP-001 |
| Docker upstream breaking update | Outage or missing migrations | Tested image digests and compatibility locks | WP-001 / releases |
| Probability numbers lack calibration | Misleading percentages | Holdout evaluation, abstention/quality thresholds | WP-004/005 |
| LLM provider overspend | Uncontrolled cost | Approved source/tool/cost limits and resumable job ledger | WP-011 |
| Corporate sync exposure of family data | Access by unintended employees | Review permissions, protect backups, optional encryption | WP-001 |
| AGPL/noncompliant derivative | Legal obligations | Licence assessment before redistribution/hosting | WP-000/release |
