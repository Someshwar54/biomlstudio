"""add_ml_workflow_job_type

Revision ID: 52c7e863e932
Revises: 
Create Date: 2025-12-03 18:39:20.769046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "52c7e863e932"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add ml_workflow to the jobtype enum
    op.execute("ALTER TYPE jobtype ADD VALUE IF NOT EXISTS 'ml_workflow'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values
    # This would require recreating the enum type
    pass
