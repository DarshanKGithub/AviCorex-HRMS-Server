"""add tenancy models

Revision ID: 0003_add_tenancy_models
Revises: 0002_ensure_employee_phone_column
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa

revision = '0003_add_tenancy_models'
down_revision = '0002_ensure_emp_phone_col'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()

    if 'tenants' not in tables:
        op.create_table(
            'tenants',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('domain', sa.String(length=255), nullable=True, unique=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'plans' not in tables:
        op.create_table(
            'plans',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('price_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('billing_period', sa.String(length=20), nullable=False, server_default='monthly'),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'plan_features' not in tables:
        op.create_table(
            'plan_features',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('plan_id', sa.String(length=36), nullable=False),
            sa.Column('feature_key', sa.String(length=120), nullable=False),
            sa.Column('is_included', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index('ix_plan_features_plan_id', 'plan_features', ['plan_id'])

    if 'subscriptions' not in tables:
        op.create_table(
            'subscriptions',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('tenant_id', sa.String(length=36), nullable=False),
            sa.Column('plan_id', sa.String(length=36), nullable=False),
            sa.Column('external_order_id', sa.String(length=128), nullable=True),
            sa.Column('starts_at', sa.Date(), nullable=False),
            sa.Column('ends_at', sa.Date(), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index('ix_subscriptions_tenant_id', 'subscriptions', ['tenant_id'])

    if 'tenant_features' not in tables:
        op.create_table(
            'tenant_features',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('tenant_id', sa.String(length=36), nullable=False),
            sa.Column('feature_key', sa.String(length=120), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index('ix_tenant_features_tenant_id', 'tenant_features', ['tenant_id'])


def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()

    if 'tenant_features' in tables:
        op.drop_table('tenant_features')
    if 'subscriptions' in tables:
        op.drop_table('subscriptions')
    if 'plan_features' in tables:
        op.drop_table('plan_features')
    if 'plans' in tables:
        op.drop_table('plans')
    if 'tenants' in tables:
        op.drop_table('tenants')
