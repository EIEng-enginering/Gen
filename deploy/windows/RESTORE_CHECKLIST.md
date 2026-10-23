# 24 Gen cold-backup restore drill — Rev A.1 review candidate

**Use disposable genealogy fixtures only. Never restore onto the only live family-history dataset.** The archives include user credentials, accepted tree data, research data and original media. Keep raw archives outside OneDrive in a restricted local directory. Any cloud export needs encryption and an access review.

1. Read `deploy/backup-volumes.json`. The source backup must contain **exactly nine** `gen24_<volume>.tgz` archives matching that manifest, plus `SHA256SUMS.txt` and `BACKUP_NOTES.txt`. Reject any directory containing `INCOMPLETE.txt`.
2. Independently verify every SHA-256 hash and inspect every archive listing. Reject absolute paths, `..` traversal, suspicious links and unexpected files. Record the backup path, hash manifest and test fixture identity in `ACCEPTANCE_REPORT.md`.
3. Use a **separate Docker context or isolated disposable Compose project**, for example `gen24restore`, with its own test-only `.env`, unique loopback ports and no production volume mounts. Confirm its volume names and `com.docker.compose.project=gen24restore` labels before extraction.
4. Create the restore project's nine volumes without starting the applications. Map each source `gen24_<key>.tgz` only to the corresponding `gen24restore_<key>` volume. Inspect the destination name and ownership label immediately before each extraction. Never infer destinations from an uncontrolled wildcard.
5. Start the isolated stack. Log in with the disposable Gramps test credentials. Verify a known test person, cited source and original media file; verify research PostgreSQL connectivity and a test query. Stop and restart the isolated stack, then repeat the checks.
6. Record archive hashes, record/media counts, screenshots, Docker/image versions, test commands, output, date and reviewer. Destroy **only** the disposable restore project after evidence has been reviewed.

This checklist does not automate restore. A guarded restore implementation and a witnessed full drill are still required before WP-001 or R0.1 is accepted.
