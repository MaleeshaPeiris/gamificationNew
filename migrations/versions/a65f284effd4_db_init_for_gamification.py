"""Db init for gamification

Revision ID: a65f284effd4
Revises: 4f4af47f606b
Create Date: 2024-05-07 18:32:23.180319

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a65f284effd4'
down_revision = '4f4af47f606b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quiz_question', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'quiz_set', ['quiz_set_id'], ['id'])

    with op.batch_alter_table('quiz_set', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'course', ['course_id'], ['id'])

    with op.batch_alter_table('quiz_submission', schema=None) as batch_op:
        batch_op.alter_column('is_correct_answer',
               existing_type=mysql.INTEGER(),
               type_=sa.Boolean(),
               existing_nullable=False)
        batch_op.create_foreign_key(None, 'quiz_set', ['quiz_set_id'], ['id'])
        batch_op.create_foreign_key(None, 'quiz_question', ['quiz_question_id'], ['id'])
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])

    with op.batch_alter_table('user_course', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])
        batch_op.create_foreign_key(None, 'course', ['course_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_course', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('quiz_submission', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('is_correct_answer',
               existing_type=sa.Boolean(),
               type_=mysql.INTEGER(),
               existing_nullable=False)

    with op.batch_alter_table('quiz_set', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('quiz_question', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    # ### end Alembic commands ###
