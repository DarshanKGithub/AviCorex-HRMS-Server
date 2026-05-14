#!/usr/bin/env bash
set -euo pipefail

# Simple helper to run migrations in CI or one-off shells.
# Usage: ./run_migrations.sh

pip install -r requirements.txt
alembic -c alembic.ini upgrade head
