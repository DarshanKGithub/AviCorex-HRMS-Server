"""add tenant_id to users

Revision ID: 0004_add_user_tenant_id
Revises: 0003_add_tenancy_models
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa

revision = '0004_add_user_tenant_id'
down_revision = '0003_add_tenancy_models'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = []
    try:
        cols = [c['name'] for c in insp.get_columns('users')]
    except Exception:
        cols = []

    if 'tenant_id' not in cols:
        op.add_column('users', sa.Column('tenant_id', sa.String(length=36), nullable=True))
        # create index
        op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
        # try adding FK if tenants table exists
        try:
            tables = insp.get_table_names()
            if 'tenants' in tables:
                op.create_foreign_key('fk_users_tenant', 'users', 'tenants', ['tenant_id'], ['id'])
        except Exception:
            pass


def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('users')]
    if 'tenant_id' in cols:
        try:
            op.drop_constraint('fk_users_tenant', 'users', type_='foreignkey')
        except Exception:
            pass
        try:
            op.drop_index('ix_users_tenant_id', table_name='users')
        except Exception:
            pass
        op.drop_column('users', 'tenant_id')
