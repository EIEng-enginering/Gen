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
