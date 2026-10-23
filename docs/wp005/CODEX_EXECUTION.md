# Codex execution instructions — WP-005 revision C

**Base commit (exact):** `6a299b1f26cbadf350a6a58297b07027d5822f66` (`feature/wp-002-evidence`).
**Repository:** `https://github.com/EIEng-enginering/Gen.git`.
**Target:** new stacked branch based on the exact WP-002–004 candidate. Do not merge existing drafts unreviewed.

1. Read `docs/wp005/README.md`, the manifest and all 50 approved decisions. Inspect remote refs/PRs #2, #3 and #1. Record clean status, exact baseline SHA and changed-file hashes.
2. Run the supplied preflight/apply helper. It refuses different baseline commits, non-clean trees or failing patch checks. Never recreate/replace the repository or delete volumes.
3. Run `python -m pytest -q apps/research-web/tests`, `python tools/validate_decisions.py`, `python -m compileall -q apps/research-web/app`, `node --check` on extracted workspace JS (or browser test) and `git diff --check`. Capture outputs.
4. Confirm the old research schema migration `20261023_001` is never changed. New revision `20261023_002` must preserve old records. Never auto-migrate a populated database on service startup.
5. On a separate disposable Windows Docker host (if available), run a live Gramps + research DB smoke and simulated family graph; complete full cold backup and isolated restore with media checksum. If Docker/Gramps unavailable, mark NOT RUN rather than claiming acceptance.
6. Verify that a proposed branch cannot edit Gramps, history is preserved across API calls and old branch versions conflict as HTTP 409. Confirm no real family data, credentials or tokens appear in logs/artifacts.
7. Submit a draft PR based on `feature/wp-002-evidence` after review of that dependency. Report commit, files, migration result and acceptance gates. Retain R0.1 NOT ACCEPTED until the earlier live Windows validation is actually witnessed.

The new `tools/evaluate_matching.py` measures quality on independently reviewed holdout CSV, but **does not calibrate** scores into percentages. Do not report synthetic test precision as genealogical accuracy.
