"""add_progress_and_result_columns

Revision ID: f7b5e4680b18
Revises: 205229cd4026
Create Date: 2025-12-03 18:55:10.380546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7b5e4680b18"
down_revision: Union[str, Sequence[str], None] = "205229cd4026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add progress column (Float) for simplified workflow progress tracking
    op.add_column('jobs', sa.Column('progress', sa.Float(), nullable=True))
    # Add result column (JSON) for workflow results
    op.add_column('jobs', sa.Column('result', sa.JSON(), nullable=True))
    # Set default progress to 0.0 for existing rows
    op.execute("UPDATE jobs SET progress = 0.0 WHERE progress IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('jobs', 'result')
    op.drop_column('jobs', 'progress')
