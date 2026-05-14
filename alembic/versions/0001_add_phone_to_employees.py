"""add phone to employees

Revision ID: 0001_add_phone_to_employees
Revises: 
Create Date: 2026-05-14
"""

from alembic import op
import sqlalchemy as sa

revision = '0001_add_phone_to_employees'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add phone column if not exists (safe for Postgres)
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('employees')]
    if 'phone' not in cols:
        op.add_column('employees', sa.Column('phone', sa.String(length=20), nullable=True))


def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('employees')]
    if 'phone' in cols:
        op.drop_column('employees', 'phone')
