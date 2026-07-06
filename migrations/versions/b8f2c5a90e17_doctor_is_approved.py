from alembic import op
import sqlalchemy as sa


revision = 'b8f2c5a90e17'
down_revision = '6ce46f1f1b55'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('doctor', sa.Column('is_approved', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.execute('UPDATE doctor SET is_approved = 1')


def downgrade():
    op.drop_column('doctor', 'is_approved')
