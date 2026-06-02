"""
Revision ID: c796235f9357
Revises: 0004_add_user_tenant_id
Create Date: 2026-06-02 10:53:09.608524
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c796235f9357'
down_revision = '0004_add_user_tenant_id'
branch_labels = None
depends_on = None



def upgrade():
    op.add_column('leave_requests', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('leave_requests', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))


def downgrade():
    op.drop_column('leave_requests', 'updated_at')
    op.drop_column('leave_requests', 'created_at')
