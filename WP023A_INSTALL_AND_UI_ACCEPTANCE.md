# WP023A Windows installation and UI commissioning report

Date: 2026-10-24 (Australia/Perth). Repository: `https://github.com/EIEng-enginering/Gen.git`. Exact parent: `feature/wp-014-016-evidence-assistant-ops` at `636eff5293dcb8c66ba29536fc35dcc81eb4a313`. Candidate: `feature/wp-023a-windows-install-ui`; six-script implementation commit `fcbfbda3f58d2aaf936e5868254d3b7c80db1475`; [draft PR #10](https://github.com/EIEng-enginering/Gen/pull/10) targeting the parent. Prior draft PRs #2 → #3 → #1 → #4 → #5 → #6 → #7 → #8 → #9 remain in dependency sequence. No merge occurred.

## Kit and source integration

- User-supplied `24Gen_Windows_Installation_UI_Commissioning_Kit_Rev_A.zip`: SHA-256 `5a4d5f88f9d1ad4b9c8cbaab05e41783825bbd552b6535c139119b0f641c7327`; 17 entries, 46,995 uncompressed bytes. Inspected for traversal, absolute paths, symlinks, case-insensitive duplicates and size limits. All 16 `SHA256SUMS.txt` entries matched before extraction outside the Git checkout.
- `APPLY_SAFE.py --verify-only` passed exact parent SHA, clean worktree, six absent targets and six source hashes. Branch `feature/wp-023a-windows-install-ui` was created from the exact SHA; `--apply` added only six `deploy/windows/*.ps1` scripts. All six installed SHA-256 values match `MANIFEST.json`. No existing file, `.env`, database, Compose volume or Gramps object was overwritten.
- The six scripts implement read-only host preflight, guarded `-DisposableTestOnly` first start, authenticated/anonymous UI smoke checks, normal start, desktop shortcuts and PowerShell syntax validation. The kit adds no migration, external provider/model executor or accepted Gramps tree-write API. Its supplied acceptance checklist remains in the inspected kit outside the repository.

## Host and checks performed

| Item | Observed result |
|---|---|
| Host | Microsoft Windows 11 Pro, build 26200; 15.8 GiB RAM. PowerShell 7.6.5 and Windows PowerShell 5.1 available; project Python 3.12.14. |
| ZIP/package contract | 16/16 hashes passed; nine kit tests passed. |
| Windows scripts | All six parsed successfully with both PowerShell 7 and Windows PowerShell 5.1; `Validate-24Gen-Scripts.ps1` passed after installation into the checkout. |
| Existing Python regression | **112 passed**, one upstream Starlette/AnyIO deprecation warning, 31.17 s, using disposable pytest base temp. |
| Decisions/dependencies | Q01–Q50 approved-decision validator passed; `pip check` found no broken requirements. |
| Git | Only the six manifest scripts in the implementation commit; staged `git diff --check` passed. Remote parent still at exact required SHA when branch was pushed. |
| WSL/Docker | `wsl.exe --version` returned WSL not installed; `Preflight-24Gen.ps1 -RequireDocker` reports WSL not ready and Docker CLI missing. Docker Engine/Compose versions unavailable. |
| Disposable installer | `Install-24Gen.ps1 -DisposableTestOnly -NoBrowser -NoShortcuts` stopped at the Docker prerequisite before `.env` creation, image pull, container creation or volume operation. `.env` remains absent. |
| Virtualization | Read-only WMI fields `VirtualizationFirmwareEnabled`, `SecondLevelAddressTranslationExtensions` and `VMMonitorModeExtensions` returned false. Treat this as an unresolved capability check, not proof that hardware lacks support; verify firmware/Task Manager and Windows feature state with the operator/IT. |
| Current listeners | No listener observed on intended UI ports 5055 and 8765 or broker port 6379. An **existing, unrelated** PostgreSQL service was listening on port 5432 at `0.0.0.0` and `::`. It was not used or changed. Its network/firewall exposure warrants separate owner/IT review. |

## Live acceptance: not performed

No five-service stack started; no image IDs or digests, Compose service status, research/Gramps HTTP response, Basic-auth 401, browser screenshot, Gramps owner login, synthetic XML import, stop/restart persistence, nine-volume cold backup or isolated restore result exists from this run. PostgreSQL migrations `20261023_001`–`007` were **not** run on the observed Windows service or any populated database. No credentials, genealogy records, media or backups were read, shared or modified. Static Compose review and the kit's contract test confirm two intended frontend bindings use `127.0.0.1` and PostgreSQL/Valkey have no Compose `ports`; actual Docker/firewall mappings remain unverified.

## Operator prerequisites and safe continuation

1. Have an administrator/operator confirm corporate permission for WSL and Docker Desktop, Docker licence eligibility, firmware virtualization, Windows optional feature state and the pre-existing PostgreSQL listener/firewall rules. Microsoft documents `wsl --install` from an Administrator PowerShell followed by a reboot. Docker's current Windows documentation specifies a working WSL 2 backend and its licence conditions; this medium-integrity session cannot activate WSL or install Docker on the host.
2. After WSL and Docker Desktop Linux containers are installed and running, on a **disposable** host/stack run `deploy/windows/Validate-24Gen-Scripts.ps1`, then `Preflight-24Gen.ps1 -RequireDocker`. Review image tags/digests and licences before production use. Keep live source/secrets/storage outside OneDrive.
3. Run `Install-24Gen.ps1 -DisposableTestOnly` and `Test-24Gen-UI.ps1 -RequireDatabase`. Record all five services, actual loopback port bindings, image IDs/digests and UI/auth outcomes without passwords. Create a separate Gramps owner with synthetic data, verify person/source/media after restart, and capture synthetic-only UI/accessibility evidence.
4. Before any real family-data use, perform the exact nine-volume cold backup in restricted local storage and an **isolated** restore with media checksums and a second persistence check. Test migrations only on an explicitly disposable PostgreSQL clone after a verified backup. Do not run automatic populated upgrades, delete volumes, or enable accepted-tree writes.

**Decision: WP023A source candidate integrated; Windows installation/UI commissioning NOT ACCEPTED; R0.1 NOT ACCEPTED.** Draft PR #10 remains open for review. The first live gate is an administrator/IT-prepared WSL2 and Docker Desktop host with licence clearance; the next gates are synthetic first boot and independently witnessed recovery.

## Host setup follow-up — 2026-10-24

The user requested WSL2 and Docker Desktop setup and confirmed Docker Desktop licence clearance. An elevated administrator UAC session successfully ran Microsoft's `wsl --install --no-distribution`: exit code 0, WSL version **3.0.3**, kernel **6.18.54.1**. Windows enabled `VirtualMachinePlatform` and explicitly reported that a **reboot is required** before the change takes effect. The separate legacy `Microsoft-Windows-Subsystem-Linux` feature remained disabled; WSL reports default version 2, with virtualization unavailable until restart.

Docker Desktop **4.96.3** was downloaded from Docker's official installer URL through winget. The 641,758,128-byte installer matched SHA-256 `3d8adad4f6c86583e0b00ea19a76197c51ccf5c83437c9ed775b739756452507` and had a valid Docker Inc. Authenticode signature. It installed successfully in **per-user WSL2 mode** after the Windows feature was enabled. Installed CLI: Docker **29.9.2**; Compose **v5.6.1**. `docker info` currently fails because there is no running engine before the required reboot. No project Compose service, `.env`, volume or genealogy database was created or changed by this host setup.

After the user saves open work and authorizes a restart, verify `wsl --status`, `wsl --version`, Docker Desktop Linux engine and `docker info`/`docker compose version`. Then rerun `Preflight-24Gen.ps1 -RequireDocker` and proceed only with the disposable commissioning checklist above. This follow-up supersedes the earlier host-availability rows; it does **not** change the R0.1 acceptance decision.

## Disposable first boot and UI follow-up — 2026-10-24

After the user approved the reboot, WSL 3.0.3 reported default version 2 and Docker Desktop's Linux engine became available. `Preflight-24Gen.ps1 -RequireDocker` passed. With the user's instruction to open the program, `Install-24Gen.ps1 -DisposableTestOnly` created a local, access-restricted `.env`, pulled the images, built the research image, and started the five-service Compose stack. The installer completed with exit code 0. The `.env` is ignored by Git; `git status --short` was clean. No existing Windows PostgreSQL database or real family data was used.

`Test-24Gen-UI.ps1 -RequireDatabase` passed: authenticated landing and research workspace pages, anonymous workspace HTTP 401, research database connection, disabled accepted Gramps tree mutation, and a responding Gramps Web homepage. The five services are running; `research_db` is healthy. Only the research UI (`127.0.0.1:8765`) and Gramps Web (`127.0.0.1:5055`) are published, both on loopback. The project has exactly nine named Compose volumes. The installer launched both URLs in the browser and created desktop Start and Open, Stop, and Check UI shortcuts.

**Commissioning remains incomplete; R0.1 NOT ACCEPTED.** Gramps owner creation/login, synthetic XML import, interactive browser checks, restart persistence, exact nine-volume cold backup and isolated restore, and production image/licence review have not been verified. Keep real genealogy data out of this disposable stack and keep accepted-tree writes disabled until those gates pass.

## Docker operation and Gramps startup repair — 2026-10-24

The user requested a working Docker installation. The research UI, PostgreSQL, Valkey and Gramps Web were running, but `grampsweb_celery` was repeatedly restarting. Its log reported Alembic revision `9c4d2e7a5b18` overlapping `a8e57fe0d82e`. A read-only SQLite check showed both revision markers, database integrity `ok`, zero users and zero trees; the installed Gramps image had only `9c4d2e7a5b18` as its head. This is consistent with simultaneous initial migrations from the web and worker containers. [Gramps Web API issue #847](https://github.com/gramps-project/gramps-web-api/issues/847) documents the maintainer's `alembic stamp --purge` repair for overlapping revision markers.

Before repair, `Backup-24Gen.ps1` stopped the stack and archived all nine verified project volumes to local restricted storage at `C:\24Gen\Backups\Restricted\gen24-cold-20261024-033108Z`. All nine archives matched the generated SHA-256 manifest; the Gramps users archive contains `users.sqlite`. **No isolated restore has been performed.** The worker was stopped, then the Gramps revision table was stamped to the already-applied head `9c4d2e7a5b18` using the maintainer procedure. A read-only follow-up found one head, integrity `ok`, and zero users. The worker restarted and remained running with zero restarts.

The Compose file now checks Gramps Web health and waits for it before starting the worker, preventing simultaneous first-start migrations. `Test-24Gen-UI.ps1` now refuses to pass unless all five services are running. Applying the revised Compose file recreated only the two Gramps containers; their existing named volumes were retained. Gramps Web became healthy before the worker started. The live UI/database/auth/write-policy checks passed in both PowerShell 7 and Windows PowerShell 5.1. The full research-web suite passed **113 tests** with one upstream deprecation warning; Compose syntax and script validation passed.

Gramps first-run owner account, empty test tree, login, synthetic import, restart persistence and isolated restore remain outstanding. The in-app browser's URL policy blocked further interactive research-page inspection; direct local HTTP checks passed. R0.1 remains **NOT ACCEPTED**.

## Local Gramps test owner and restart persistence — 2026-10-24

With explicit user approval, a local `gen24-test-owner` (role 4, Owner) was created through Gramps's own CLI and bound to the existing empty `24 Gen` tree `bcb2c12d-c1a3-4877-8603-0feab6a1d471`. A cryptographically random password was saved at `C:\24Gen\Secrets\Gramps-Local-Test-Owner.txt`, outside OneDrive. The file ACL grants only the current Windows user, Administrators and SYSTEM full access; no password or token was printed in the report or Git. An initial Windows-to-container pipe appended a carriage return to the password. This was corrected through Gramps's authenticated password-change API, and the saved password was then verified by a successful local token login.

The first-start migration race also created a second, unassigned `24 Gen` tree at `e83c402a-13ca-4379-adc6-a245336c00b2`. Read-only SQLite counts showed **zero** people, families, sources, citations, events, media, places, repositories and notes in both trees. The owner sees only the intended tree. The extra empty tree was retained to avoid deleting any existing volume data during commissioning.

Gramps Web and its worker were stopped and restarted with the new health dependency; all five services passed the live smoke check afterward. A fresh authenticated Gramps API login returned the same tree ID after restart. Thus owner login and empty-tree persistence across container restart are **verified**. A synthetic XML import, media persistence, real browser interaction and isolated restore are still unverified. The pre-owner nine-volume cold backup has verified archive hashes but has not been restored. **R0.1 remains NOT ACCEPTED.**
