# 24 Gen repository baseline — 23 October 2026

## Target repository

- Exact remote: `https://github.com/EIEng-enginering/Gen.git`.
- GitHub connector: 404 for the linked app account; that account has no installation on the named organization.
- Direct Git access: `git ls-remote ... HEAD` succeeded with no refs, and cloning the exact URL reported an empty repository. The cloned `main` HEAD had no commit, no tracked files and no existing functionality to preserve.
- The first local baseline commit on `main` is `eb4abe1` (`Initialize 24 Gen repository baseline`). This is a new baseline for the previously empty target, not a pre-existing project SHA.
- Local integration branches: `feature/wp-000-governance` at `3ae6faf`; `feature/wp-001-foundation` contains `459a559` and corrective commit `fe8eb6c`. The latter branch starts from WP-000, preserving package order.
- The WP-001 branch includes acceptance evidence at `fed73de`. After the user explicitly authorized publication to the exact URL, `main`, `feature/wp-000-governance`, and `feature/wp-001-foundation` were pushed. Remote refs were verified: `main=eb4abe1`, `WP-000=3ae6faf`, `WP-001=ed3247e` before this report update. No PR was created because the GitHub connector remains unauthorized for the organization and the in-app browser is not signed in.
- This checkout is an integration and review clone in the OneDrive project folder. A separate active clone of the published WP-001 branch now exists at `C:\24Gen\Gen`, outside OneDrive. Neither checkout has a generated `.env` or live genealogy data.

## Source and overlay review

- Source: `24Gen_Master_Development_Package_Rev_A.zip`, SHA-256 `B44C972BDCE5F85EFB28EA2785E61029FB48459F80D6646090F204FCC3427884`.
- Corrective guidance: `24Gen_Codex_Next_Action_After_Report_Rev_A1.md`. It mentioned a supplied replacement script, manifest, tests and checklist, but those separate files were absent. The correction here was authored from the Markdown requirements and is marked as a review candidate.
- The exact remote had no files, so there were no overlay path conflicts or existing behaviours to merge. WP-000 added governance and docs, followed by WP-001 scaffold files. No migration, accepted family data or credentials were copied.
- Changes relative to `main`: `git diff --stat main...feature/wp-001-foundation`. Review each commit separately before merge.

## Host/toolchain

- Windows registry reports ProductName `Windows 10 Pro`, build `26200`; PowerShell `7.6.5`; Git `2.54.0.windows.1`.
- Python `3.12.14` virtual environments were created in the offline development checkout and `C:\24Gen\Gen`. The WP-001 development requirements installed successfully under the recorded Windows constraint file in the active clone, and all eight tests plus decision validation passed there.
- WSL reports that the Windows Subsystem for Linux is not installed. Docker Desktop executable and Docker CLI are absent. No Compose start, Gramps import, container image compatibility, backup or restore drill was performed.
- `wsl --install --no-distribution` exited 1 and repeated that WSL is not installed; no successful WSL setup was observed. The installation may require a Windows administrator session and restart.

## Release state

**WP-000 local checks pass. WP-001 remains a candidate. R0.1 is NOT ACCEPTED.** See `ACCEPTANCE_REPORT.md` for test evidence and blockers. Image digests, licence review, on-device persistence and isolated recovery remain outstanding.
