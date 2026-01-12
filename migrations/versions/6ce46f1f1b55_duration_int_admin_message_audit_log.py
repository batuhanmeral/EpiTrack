from alembic import op
import sqlalchemy as sa


revision = '6ce46f1f1b55'
down_revision = 'd4e1a9026310'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('admin',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fullname', sa.String(length=100), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('actor_role', sa.String(length=10), nullable=True),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('actor_name', sa.String(length=100), nullable=True),
    sa.Column('action', sa.String(length=20), nullable=True),
    sa.Column('entity', sa.String(length=30), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.Column('details', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('doctor_id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('sender_role', sa.String(length=10), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['doctor_id'], ['doctor.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('seizure', schema=None) as batch_op:
        batch_op.alter_column('duration',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.Integer(),
               existing_nullable=True,
               postgresql_using='duration::integer')


def downgrade():
    with op.batch_alter_table('seizure', schema=None) as batch_op:
        batch_op.alter_column('duration',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=20),
               existing_nullable=True)

    op.drop_table('message')
    op.drop_table('audit_log')
    op.drop_table('admin')
