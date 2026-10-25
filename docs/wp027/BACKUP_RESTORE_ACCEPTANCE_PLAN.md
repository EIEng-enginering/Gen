# WP-027 — Live Windows installation, image lock and recovery qualification

## Safety prerequisites

- The stack installed and running at `C:\24Gen\Gen` on an administrator-controlled Windows/Docker Desktop test host.
- Existing main `gen24` Compose project must remain untouched by this kit except normal read-only inspection. Never call `docker compose down -v` for production.
- Credentials, local runtime data and raw cold archives are stored outside OneDrive; restricted ACLs established by WP-025.
- Required nine source volumes exactly match `deploy/backup-volumes.json`.
- The backup is known to be genuine, from an approved test dataset, and its source hash is documented.

## Gates and commands

1. Run `deploy/windows/Test-24Gen-BackupIntegrity.ps1 -BackupDirectory C:\24Gen\Backups\Restricted\gen24-cold-... -RequireNonemptyMedia`. Verifies exact archive manifest, SHA-256 and tar member types. If it fails for empty media, first seed a **separate disposable Gramps test tree** with an artificial media fixture, create a new backup of that test project, then test its restore. Do not seed production just to pass a test.
2. Run `deploy/windows/Invoke-24Gen-IsolatedRestore.ps1 -BackupDirectory ... -RestoreProject gen24wp027restore1 -RequireNonemptyMedia`. This is a safe dry run and refuses existing restore volumes.
3. Run the same command with `-Execute` only with explicit approval. This creates nine *new* isolation-labelled volumes and expands archives into them; **no existing volumes are overwritten or deleted**. It does not start services or claim data usability. A separate isolated Compose instance must be set up by Codex and configured to use those volumes with new ports, unique secrets and no production app/data connections.
4. Verify original and isolated row counts, user/granps databases, full genealogical person/family/event/citation counts, media file path/hash of an explicitly nonempty synthetic fixture, basic authenticated UI, API read-only Guest access and persistence across isolated restart. Record counts/hashes without copying private records to reports.
5. Run `deploy/windows/Get-24Gen-DeploymentEvidence.ps1`. Record actual five-service versions, digests and localhost port bindings. Pin tested registry digests in a reviewed Compose override, and rerun smoke+recovery tests after pinning. This script reports digests but **does not automatically pin** them.
6. Verify PowerShell scripts via `deploy/windows/Validate-24Gen-Scripts.ps1`, Python tests, local UI/Gramps endpoints, database revision `20261025_009` against a **disposable copy** of schema revision 008, and the acquisition-workspace authorization tests.
7. Any reported missing media, source mismatch, denied owner login, private genealogy export, unexplained migration data changes or unexpected external network connection blocks R0.1 acceptance. No accepted-tree mutation is enabled.

## Acceptance output

Produce a dated `ACCEPTANCE_REPORT.md` with actual host Windows/WSL/Docker versions, tested image digests and licences, service count (**five** services), Gramps API version, proof of nine-volume restore, exact nonempty media checksum agreement, database migration before/after hashes, authentication/UI screenshots from synthetic fixtures and reviewed known defects.

All test evidence must be privacy safe. Retain sensitive backup material locally in the restricted backup location, never in Git/OneDrive without separate approved encryption.
