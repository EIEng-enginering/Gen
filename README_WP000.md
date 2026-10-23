# WP-000 — Repository Quality Baseline

Read `docs/MASTER_SOFTWARE_DEVELOPMENT_SPECIFICATION_REV_A.md` first. Enforce all 50 approved requirements. Source changes are additive, reviewed and regression tested. Never commit `.env`, genealogical records or living persons' documents. See `.github/workflows/quality.yml` and `tools/validate_decisions.py`. CI checks baseline decisions and, if WP-001 has been integrated, its Python tests. In future add mypy/ruff/secret scanning with explicit locked versions and independent acceptance evidence.
