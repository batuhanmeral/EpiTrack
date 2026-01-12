from alembic import op
import sqlalchemy as sa


revision = 'd4e1a9026310'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('doctor',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fullname', sa.String(length=100), nullable=False),
    sa.Column('tcno', sa.String(length=11), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tcno')
    )
    op.create_table('patient',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fullname', sa.String(length=100), nullable=False),
    sa.Column('tcno', sa.String(length=11), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('bloodtype', sa.String(length=5), nullable=True),
    sa.Column('birthdate', sa.Date(), nullable=True),
    sa.Column('doctorid', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['doctorid'], ['doctor.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tcno')
    )
    op.create_table('seizure',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('patientid', sa.Integer(), nullable=False),
    sa.Column('seizuretime', sa.DateTime(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('trigger', sa.String(length=100), nullable=True),
    sa.Column('postictal', sa.String(length=200), nullable=True),
    sa.Column('duration', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['patientid'], ['patient.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('seizure')
    op.drop_table('patient')
    op.drop_table('doctor')
