#!/bin/sh
set -eu
# Initialize only a genuinely empty DB; NEVER silently upgrade existing data.
# A populated schema change requires a verified backup and an explicit operator
# migration + rollback plan.
python -m app.research.schema_gate
exec uvicorn app.main:app --host 0.0.0.0 --port 8765
