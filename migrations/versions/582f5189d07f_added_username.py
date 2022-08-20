"""added username

Revision ID: 582f5189d07f
Revises: 0841ade35183
Create Date: 2022-08-16 11:28:46.219376

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '582f5189d07f'
down_revision = '0841ade35183'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('username', sa.String(length=20), nullable=False))
    op.create_unique_constraint(None, 'users', ['username'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'username')
    # ### end Alembic commands ###