# WP-012 / WP-013 integration and acceptance gates

1. Verify exact parent `feature/wp-010-011-provenance-jobs` at `51016ac5c19b338512df14f9cc093c87e3fbb181` or STOP. Reconcile independently if branch moves.
2. Inspect existing draft PRs #2 -> #3 -> #1 -> #4 -> #5 -> #6 -> #7; do not merge them solely to install a new overlay.
3. Apply overlay on a new stacked branch only after clean status, exact source checksums and dry-run Git patch validation.
4. Run the whole Python suite, Q01-Q50 register validator, `python -m pip check`, Python compile and browser JavaScript syntax.
5. Test authenticated manual source-family linking across different declared origins, read-only tree/compare API and unknown option. Test a malicious record label to ensure it stays plain text.
6. If a disposable PostgreSQL instance is available, run all previous migrations and test chart endpoints; no migration is introduced in WP-012/013. Never auto-migrate the observed Windows PostgreSQL service.
7. Verify live Gramps GET-only compatibility, local-only Docker bind, nine-volume cold backup and isolated restore separately. Do NOT mark R0.1 accepted without these gates.
8. Record baseline SHA, changed-path manifest, commit SHA, test evidence, remaining blockers and a draft pull request. Never store living-person details, credentials or raw backups in Git.

No accepted-tree writes, third-party record searches, paid AI usage or calibrated genealogy probabilities are authorised by this package.
