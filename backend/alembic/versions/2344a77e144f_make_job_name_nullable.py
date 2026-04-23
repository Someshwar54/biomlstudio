"""make_job_name_nullable

Revision ID: 2344a77e144f
Revises: 52c7e863e932
Create Date: 2025-12-03 18:41:27.875168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2344a77e144f"
down_revision: Union[str, Sequence[str], None] = "52c7e863e932"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('jobs', 'name',
                    existing_type=sa.String(length=255),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('jobs', 'name',
                    existing_type=sa.String(length=255),
                    nullable=False)
