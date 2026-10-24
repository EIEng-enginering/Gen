# AI Research — Test and Acceptance Gates

| Gate | Local package result | Required on Windows |
| --- | --- | --- |
| Source archive verifies | PASS | Reconfirm exact Git parent and diff |
| Approved decisions Q01–Q50 | PASS | Preserve in PR |
| Existing and new Python tests | PASS (121, 27 warnings) | Run under Windows Python 3.12 |
| Citation-forgery, auth, model-schema and manual-only tests | PASS with synthetic records | Add further hard negatives and model evaluation |
| Source-group evidence check | PASS (conservative, no independence proof) | Review with real imported record formats |
| Schema migration 007→008 | PASS with disposable SQLite; populated downgrade refused | Disposable PostgreSQL migration and restore drill required |
| Browser JavaScript syntax | PASS | Full browser controls and screenshots on Windows required |
| Local Ollama real inference | NOT RUN (model unavailable in this environment) | Configure local model and run cited synthetic case |
| Live Gramps read-only context | NOT IMPLEMENTED by this package | Verify Gramps person/family GET semantics and add context bridge |
| Provider automated queries | DISABLED (by design) | Rights verification and scoped connector development |
| Local UI and authenticated service | API tests pass; Chromium navigation blocked by administrator in this environment | Interactive smoke on actual Windows computer |
| Docker Compose / backup | Compose YAML parsed; no Docker installed here | Five services; nine-volume cold backup & isolated restore |
| Production release | NOT ACCEPTED | Review full matrix before live genealogy records |

**Do not merge or mark the AI feature complete solely because mocked local-model tests pass.**
