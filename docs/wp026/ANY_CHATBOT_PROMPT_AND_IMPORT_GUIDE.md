# AI research prompt generator — any chatbot

Open **http://127.0.0.1:8765/acquisition** once installed. Enter surname (e.g. Oldham), historic area (e.g. Cheshire), start/end year, mode; press **Build source-controlled research prompt**. Copy the result to ChatGPT, Claude, Gemini, Grok or another capable model. It will instruct that model to return individual source-cited records as plain JSONL **only when it has actually accessed allowed historical records**. No invented sources and no public-search scraping.

- `guided`: step-by-step source tasks, review at each action.
- `conventional`: search suggestions and explicit source audit.
- `autonomous`: task planning only. The supplied application does NOT run any external model searches or historical-provider API calls automatically.

For multiple families/areas run:

```powershell
cd C:\24Gen\Gen
python tools\build_ai_research_shards.py --surnames "Oldham,Bardsley" --areas "Cheshire,Lancashire" --start 1750 --end 1900 --step-years 25 --out C:\24Gen\ResearchPrompts\ShardSet001
```

The task manifest contains suggested prompts with **status `not_searched`**. The model must disclose access restrictions and which tasks were actually performed. Do not paste sensitive living-person names into third-party chatbots.

For a few records paste JSONL directly into the acquisition page and attest rights; for more use the local streaming script:

```powershell
python tools\stream_evidence_jsonl.py C:\24Gen\Imports\approved_records.jsonl --format jsonl --input-kind user_export
# After validation and backup approval:
python tools\stream_evidence_jsonl.py C:\24Gen\Imports\approved_records.jsonl --format jsonl --input-kind user_export --confirm-rights --execute
```

`--execute` stages, **not approves**. It requires `GEN_ADMIN_USER` and `GEN_ADMIN_PASSWORD` already available in the current PowerShell environment; do not put passwords in command lines, tickets or Git.

The JSONL schema is represented by `fixtures/synthetic_cheshire_intake.jsonl`, containing **invented** data only. Mandatory keys include `provider`, `provider_record_id`, `source_title`, `source_reference`, `record_type`, `person_name_verbatim` for non-leads, `access_method`, `licence`, `rights_note`, `origin_group` and `extraction_status`.

Promoted records remain independent research observations and never automatically edit Gramps. A source citation/index is not independently verified genealogy proof.

## Adapting licensed exports with different columns

For a genuinely permitted export, create a JSON mapping with explicit `columns` from vendor CSV header names to 24 Gen field names and fixed `defaults` for provenance/permission fields; see `fixtures/synthetic_csv_field_mapping.json`. Run:

```powershell
python tools\map_source_csv.py C:\24Gen\Imports\licensed_input.csv C:\24Gen\Imports\source_mapping.json C:\24Gen\Imports\converted.jsonl
```

The converter validates each record, refuses overwriting and never invents source references or permissions. Inspect the converted records before using the streaming staging script. The synthetic example is not a licence for the actual provider export.
