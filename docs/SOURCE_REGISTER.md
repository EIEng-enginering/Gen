# Reference Register and Verification Notes

**Date checked:** 2026-10-23. Documentation URLs were checked during master-spec preparation. Licence or API approvals are **not** implied by links.

| Source | Authoritative URL | How used |
| --- | --- | --- |
| Gramps Web Docker deployment | https://www.grampsweb.org/install_setup/deployment/ | Compose, persistence and first-run owner setup |
| Gramps Web official Compose sample | https://github.com/gramps-project/gramps-web-docs/blob/main/examples/docker-compose-base/docker-compose.yml | Worker, Valkey and volume layout |
| Gramps Web Swagger | https://www.grampsweb.org/development/backend/api/ | API discovery and contract check |
| Gramps Web API source | https://github.com/gramps-project/gramps-web-api | Upstream integration and licences |
| Docker Desktop WSL2 | https://docs.docker.com/desktop/features/wsl/ | Local Windows environment |
| FamilySearch Developer | https://developers.familysearch.org/ | Registration and explicit permission limits |
| Free UK Genealogy bulk data | https://www.freeukgenealogy.org.uk/bulk-data-for-research/ | Data licensing enquiry, not automatic permission |
| FreeBMD | https://www.freebmd.org.uk/ | Assisted manual search until authorised licence |
| FreeREG | https://www.freereg.org.uk/ | Parish research |
| FreeCEN | https://www.freecen.org.uk/ | Historical census research |
| GRO England and Wales | https://www.gov.uk/research-family-history | Civil registration |
| The National Archives Discovery | https://discovery.nationalarchives.gov.uk/ | Historical archive references |
| Splink | https://moj-analytical-services.github.io/splink/ | Probabilistic identity linkage design |
| GEDCOM 7 | https://gedcom.io/specifications/FamilySearchGEDCOMv7.html | Portable genealogy exchange |

## External integration release gates

1. Validate the upstream licence for Gramps, Gramps Web and other components, including AGPL obligations when redistributing or modifying covered software.
2. Confirm current upstream image tag **and immutable digest** and record it in a release-lock manifest. Never ship `latest` as a production release pin.
3. Confirm Swagger endpoint/shape against the running version; never assume endpoint paths remain stable.
4. Obtain provider-specific access authorisation before automated historical record retrieval. Manual-only sites are not machine search providers.
5. Validate provider data reuse, local retention, privacy, API limits, attribution and embedding rules independently of technical accessibility.
6. Confirm Windows/WSL/Docker licence and computer compatibility before installation.
