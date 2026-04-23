"""add_uppercase_ml_workflow

Revision ID: 205229cd4026
Revises: 2344a77e144f
Create Date: 2025-12-03 18:52:01.647147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "205229cd4026"
down_revision: Union[str, Sequence[str], None] = "2344a77e144f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add ML_WORKFLOW (uppercase) to match existing enum value pattern
    op.execute("ALTER TYPE jobtype ADD VALUE IF NOT EXISTS 'ML_WORKFLOW'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
