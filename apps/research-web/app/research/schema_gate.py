"""Boot-time schema gate: initialize EMPTY DBs, refuse unapproved upgrades.

Never run an upgrade against an existing populated database automatically.
Operators must take an independently tested backup and then execute Alembic
upgrade manually for later migrations.
"""
import sys
from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from app.research.db import engine


def check_schema():
    root=Path(__file__).resolve().parents[2]
    config=Config(str(root/'alembic.ini'))
    config.set_main_option('script_location',str(root/'migrations'))
    script=ScriptDirectory.from_config(config)
    heads=set(script.get_heads())
    if len(heads)!=1:
        raise RuntimeError('Multiple migration heads; release review required')
    bind=engine()
    with bind.connect() as conn:
        current=MigrationContext.configure(conn).get_current_revision()
        names=set(inspect(conn).get_table_names())
    if current in heads:
        return 'schema_current'
    if current is None and not (names-{'alembic_version'}):
        command.upgrade(config,'head')
        return 'initialized_empty_database'
    raise RuntimeError('Existing research database needs reviewed migration and backup; refusing automatic upgrade')


def main():
    try:
        print('24 Gen research schema:',check_schema(),flush=True)
    except Exception as exc:
        print('24 Gen research schema start REFUSED:',str(exc),file=sys.stderr,flush=True)
        raise SystemExit(1)

if __name__=='__main__':main()
