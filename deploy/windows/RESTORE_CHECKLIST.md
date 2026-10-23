# Data/media restoration — controlled drill (WP-001)

**Do not run restore onto the only live family-history dataset.** Backups contain passwords, living-person data and original media. Restrict OneDrive permissions appropriately.

1. Obtain a stopped-volume backup produced by `Backup-24Gen.ps1`, with its SHA256SUMS and notes. Check all expected nine `gen24_*` volumes are present. Do not trust a partial archive.
2. Validate SHA-256 hashes independently before extracting; inspect each `.tgz` archive listing with `tar -tzf` (no suspicious absolute or traversal paths).
3. On a **separate Docker context/machine or isolated disposable test stack**, use a distinct Compose project name such as `gen24restore`, a test-only `.env`, and unpublished ports. Create volumes using `docker compose -p gen24restore -f deploy/compose.yaml create` without starting applications. Never mount or change production volumes in the test stack.
4. For each archived original volume `gen24_X`, restore archive bytes only into the matching *test* volume `gen24restore_X`. Example conceptual shell: `docker run --rm -v gen24restore_X:/data -v BACKUPDIR:/backup alpine:3.20 sh -c 'tar -xzf /backup/gen24_X.tgz -C /data'`. Replace X, BACKUPDIR and archive names carefully; verify test volumes before extraction.
5. Start isolated test Compose stack with separate test ports. Log in with restored Gramps test credentials. Verify a known test person, recorded source reference and original media image open correctly. Verify research Postgres connect and a test query. Stop/restart and repeat persistence checks.
6. Record file/record counts, screenshots, archive SHA-256, test stack version, date and reviewer in `ACCEPTANCE_REPORT.md`; destroy *only* the disposable restore environment after sign-off.

**Important:** The illustrative command in step 4 is not an automated recovery script. The external coding engineer must make and independently test a guarded restore tool before WP-001 / Release 0.1 can be accepted. A successful backup does not prove recoverability.
