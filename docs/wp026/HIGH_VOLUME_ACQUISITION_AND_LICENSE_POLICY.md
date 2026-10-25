# WP-026 — High-volume England and Wales genealogy research intake

**Status:** Development code, no site searches and no real historical records acquired by this package. All source access must be licensed or permitted by its actual terms. Last researched 2026-10-25.

## The three collection channels

1. **Approved bulk / exported files, highest throughput:** Request a signed extraction licence from Free UK Genealogy (FreeBMD, FreeREG, FreeCEN) for a bounded county, period and field list, or ingest documents and downloads you are lawfully permitted to store. Authorisation is project- and data-specific; fee, attribution, retention and deletion terms must be registered. CSV/JSONL can be transformed locally into the strict intake record format, then staged in 100-record idempotent chunks. The CLI makes no outside requests.
2. **Manual assisted online research:** Human operator uses Cheshire BMD, Archives and Local Studies, GRO, Free UK Genealogy and other permitted websites in their browser. AI produces search formulations and organises records actually supplied. Index/citation descriptions are not the same as certificate or register contents. Enter one accurate source reference per result and link copies of one original.
3. **Model-independent delegated chatbot prompt:** A prompt shard describes surname, county, years, record types, variants, conflicts and exact JSONL schema. ChatGPT, Claude, Gemini, Grok or a future model can return researched evidence only when it really accessed allowed material. If no allowed web access exists, it must return search leads, not fabricated historical entries. Copy the returned JSONL to intake; every row remains unverified until a human checks its source.

## Source acquisition matrix and restrictions

| Collection | Useful records | Acquisition rule / blocker | Ingest route |
|---|---|---|---|
| FreeBMD | Civil B/M/D index 1837 onward | Public search only manual. No programmatic query submissions; substantial reproductions restricted. Request licensed bulk through Free UK Genealogy. | Individual manual citation or approved licensed CSV |
| FreeCEN | 19th-c. census transcriptions | Public search manual only; current terms prohibit reproduction of extracted data in any form. Store no public-site rows in 24 Gen. Bulk access requires a separate Free UK Genealogy agreement. | Licensed extract only, with written permission reference |
| FreeREG | Parish register transcripts | Treat as manual-only by default until terms specifically checked; bulk via written Free UK Genealogy agreement. | Individual manual reference or licensed CSV |
| Cheshire BMD | Local registration indexes | Manual index search; no general permission for automatic scraping. Certificate purchase/registrar access distinct. | Manual index lead with exact details |
| Cheshire Archives | Parish, will, poor law, nonconformist, county collections | Catalogue and physical/digital holdings subject to collection-specific permissions. | Catalogues remain leads; reviewed images/register extracts separate |
| GRO England/Wales | Civil registrations and certified records | Comply with available public interfaces, charges and certificate conditions. No API access assumed. | Manual/source-licensed records |
| FamilySearch | Tree, historical records and images | Developer API application/approval required; historic record search not automatically available via API. Restricted images may require provider visit. | Allowed downloaded records; persistent external link when not permitted to store |
| Findmypast, Ancestry | Census, register, newspaper, probate and user trees | Contract/subscription and downloaded-data rights required. No credential sharing or scraping. | User-provided exports with proven licence |
| National Archives Discovery | Catalogue descriptions | API access via application/email, rate restrictions and NO API result caching per current terms; catalogue is not an inspected historical record. | Human search leads, links; do not save raw API response without separate permission |
| Probate, directories, local archives | Family events / relationships and addresses | Determine holding archive, copyright and digitisation rights individually. | Rights-checked user documents or manual entries |
| GEDCOM / Gramps XML | Existing family-tree assertions | Import through Gramps for tree context; not proof of underlying source. | Gramps tree only; cited documents through separate intake |

Source terms and references:
- https://www.freebmd.org.uk/terms.html
- https://www.freecen.org.uk/terms-and-conditions
- https://www.freeukgenealogy.org.uk/bulk-data-for-research
- https://www.nationalarchives.gov.uk/terms-and-conditions/discovery-for-developers-about-the-application-programming-interface-api/
- https://developers.familysearch.org/main/docs/compatibility-review-process
- https://www.cheshirebmd.org.uk/
- https://www.cheshirearchives.org.uk/

**Permission cannot be inferred from public accessibility or AI output.** The provider register is advisory, not a legal opinion or automatic rights authority. Site conditions change and should be reviewed for the actual records and intended storage/use.

## Practical large-scale ingestion

- Prioritise county, registration district, historic parish and family networks. Use names, variants and overlapping times (e.g. 1800–1820, 1820–1840), but use deterministic boundaries in the manifest to reduce search duplication.
- Keep **one source document** (original register sheet, census folio, certificate, etc.) distinct from **one or more person observations** appearing within it. The intake schema supports an original group and an entry key.
- Maintain literal historical names, dates and locations; never collapse a baptism into a birth date, burial into death date, or a census relationship into a legal family link.
- Store provenance as: provider, provider ID, holding collection, volume/folio/page/entry, record type, transcript, original URL or offline acquisition path, access method, rights basis, permission identifier, examiner, origin group, and chronological scope.
- Stage all entries. The auto-created `staged_evidence` table is a quarantine, **not a verified genealogy database**. Only checked source entries can become SourceDocument + Observation records. Catalogues can stay as leads.
- Retain copies of the same original and flag their dependence before deriving family conclusions. The existing WP-010 source-family register is authoritative for manually attested copies; do not simply trust distinct provider labels.
- Do not feed living relatives' personal data to third-party chatbots without explicit permission and privacy controls. This release generates prompts from surname/region/year scope, not private Gramps context.
- The user may ask 100+ chatbot shards across historical eras and areas, but *results must be actually verified*. `tools/build_ai_research_shards.py` creates prompt files and a task ledger; it never searches the internet itself.

## Work still outstanding

- Large licensed extracts need source-specific field adapters and signed permission records.
- This implementation stages JSONL/CSV and requires human review individually; it is not a million-record automatic proof engine.
- Actual automated discovery must be implemented only through separately reviewed provider-specific legal API contracts, with enforceable rate/spend limits, permitted caching and test coverage.
- Original images need rights-aware checksum storage, encrypted backup, HTR transcription and viewer integration.
- Real probabilistic matching needs independently labelled/calibrated historical data and evidence dependence controls.
