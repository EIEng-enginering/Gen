# Quality, Security and Licence Register — Rev A

## Data preservation

Gramps accepted tree and custom hypotheses have separate authorities. Never overwrite original images, original text or source access terms. Imports use quarantine, duplicate warning and reversible mapping. Gramps API is the sole supported write path for approved changes.

## Safety of local-only deployment

Q14(B) means a local single-machine installation with password and ordinary backups. Docker must publish all web ports to 127.0.0.1 only. No internet sharing, tunnel, router port forwarding, UPnP or public reverse proxy. A separate security design review is compulsory before external hosting. Use random passwords in untracked `.env`. Do not commit individual credentials or living persons' records.

## Historical-provider access

API or commercial site accessibility does not automatically grant indexing, scraping, storage, AI processing or redistribution rights. Each source connector has automated permission, data retention, attribution and rate-limit fields. Where only manual use is authorised, show links/instructions rather than submit scripted requests. Check the precise current terms before every source integration.

## Software licences

Gramps Web and API are AGPL-family open-source projects. Confirm all licence versions and compliance triggers before modifying, hosting to others or distributing derived components. Keep attribution and legal notices. Image and research data rights are separate from code rights.

## Release blockers

- Git repository not inspectable or repository changes not reviewed.
- Any external network publishing of localhost services.
- No verified consistent complete backup and restore (accepted data plus media).
- API contracts or container images not pinned and compatibility-tested.
- Data model changes without migration and rollback plan.
- Probability UI showing uncalibrated numeric certainty.
- Unapproved accepted-tree mutation and paid source transactions.
