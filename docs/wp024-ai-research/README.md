# 24 Gen local-first AI Research — Implementation Candidate

## Added in this package

- Prominent **AI Research** entry point at `/workspace#ai-research` and from the research homepage; no external frontend assets.
- Authenticated `GET /api/v1/research/ai/capabilities`, `POST /ask`, `GET /history`, and `GET /history/{run_id}`.
- Local Ollama JSON adapter with endpoint allow-list (`127.0.0.1`, `localhost`, `host.docker.internal`, `ollama`), fixed port 11434, 30-second request timeout, 64-KiB response limit, bounded context, no redirects and environment-proxy bypass.
- Cited server-side retrieval from the separate research database (six observations maximum), with optional surname/county/year filters or explicit cited observation UUIDs. No unbounded model SQL tools or direct Gramps mutations.
- The model must return a fixed four-field JSON object. Unknown observation citations, invalid schema or failure produce a **clearly labelled deterministic fallback**; only locally retrieved, source-backed facts are represented as observed facts.
- Source-copy / possible-original-group warning, explicitly unverified independence, uncalibrated relationships, and manual-only FreeBMD / FreeREG / FreeCEN / Discovery suggestions. None is searched by the application.
- Locally persisted question, scope, answer, execution origin and model name. Revision `20261024_008` is additive; populated downgrade refuses data loss.
- Synthetic Cheshire Oldham tests and a Windows AI-readiness check.

## Windows model setup (explicit operator action)

The application does not download or start a language model automatically. Install [Ollama](https://ollama.com/) on an approved local Windows machine, select a model suitable for available RAM/VRAM, and explicitly pull it; for example:

```powershell
ollama pull gemma3:4b
ollama list
```

The example tag is **not** a performance or genealogy validation claim; model selection and storage needs must be measured on the target computer. Configure the **private, untracked** `C:\24Gen\Gen\.env` with:

```dotenv
GEN_LOCAL_AI_MODEL=gemma3:4b
```

The included Docker Compose configuration uses `GEN_LOCAL_AI_URL=http://host.docker.internal:11434` inside `research_web`. Verify that the container can reach the locally running Ollama server *without opening its port to a public network*. If Docker Desktop networking prevents this, resolve it using an approved local-only network design, not arbitrary `0.0.0.0` exposure. The API supports an explicit local `GEN_LOCAL_AI_URL` when running outside Docker; only fixed known local hostnames and port 11434 are accepted.

With a reviewed backup and isolated restore already demonstrated for the populated research database, perform a **manual** upgrade on a disposable PostgreSQL clone first:

```powershell
# Example only; do not run against production without an approved restore drill.
docker compose --project-directory C:\24Gen\Gen --env-file C:\24Gen\Gen\.env -f C:\24Gen\Gen\deploy\compose.yaml run --rm research_web python -m alembic upgrade 20261024_008
```

The application refuses startup on an old populated schema until the migration has been explicitly reviewed and run. Empty databases can initialise through the existing schema gate. After controlled integration/rebuild, check:

```powershell
.\deploy\windows\Test-24Gen-UI.ps1 -RequireDatabase
.\deploy\windows\Test-24Gen-AI.ps1
```

The AI check does not perform a live inference. In the authenticated browser, open `http://127.0.0.1:8765/workspace#ai-research`, enter a synthetic question and retrieve a source-cited answer. A real-model acceptance pass requires a separately observed model-generated answer from the selected local model and a restart/persistence drill.

## Important limitations

1. A configured local model has not been demonstrated running on the Windows host in this handoff; local inference is exercised against a synthetic Ollama-compatible transport in automated tests, not a real LLM.
2. Imported Gramps family-tree **person details are not automatically retrievable by this new panel**. It searches the *research database* and links to the existing provisional evidence/tree interface. A future, version-checked Gramps read-only person-context adapter is needed for complete imported-tree use.
3. No authorised genealogy-provider API executor, HTR/OCR, calibrated probabilities, external billable AI, autonomous provider worker, or accepted Gramps tree write adapter is introduced.
4. The model's prose is labelled **unverified interpretation** even when it cites a known observation. Cited record fields originate only from the server's stored records; model quotations and factual conclusions are not independently proved.
5. `autonomous` means a local plan only. No outside requests, billable operations, or accepted-tree edits can be caused by an assistant answer.
6. The user remains responsible for checking historical record rights, living-person privacy and genealogy proof arguments. No real Oldham records were included in this package.

## Protected interfaces

The research endpoints require existing HTTP Basic credentials. POST `/ask` also requires `X-24Gen-Intent: research` and same-origin checking. Conversation history is stored only in the local research database, not committed or uploaded to an external model. Secrets are never returned to the browser. The Ollama adapter contains no external-source or write tools.
