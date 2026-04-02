"""fix mapping names
Revision ID: 176f0630bb8b
Revises: c6a8f927fbf4
Create Date: 2026-04-02 16:43:40.793104
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '176f0630bb8b'
down_revision = 'c6a8f927fbf4'
branch_labels = None
depends_on = None

def upgrade():
    # 1. СТРАТЕГІЯ ДЛЯ ТАБЛИЦІ CLIENT (з перенесенням даних)
    op.add_column('client', sa.Column('enc_name', sa.Text(), nullable=True))
    op.add_column('client', sa.Column('enc_email', sa.Text(), nullable=True))
    op.add_column('client', sa.Column('enc_phone', sa.Text(), nullable=True))
    
    # Переносимо дані: копіюємо з 'name' в 'enc_name' і т.д.
    op.execute("UPDATE client SET enc_name = name, enc_email = email, enc_phone = phone")
    
    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.drop_column('phone')
        batch_op.drop_column('name')
        batch_op.drop_column('email')

    # 2. СТРАТЕГІЯ ДЛЯ ТАБЛИЦІ SERVICE
    op.add_column('service', sa.Column('enc_name', sa.Text(), nullable=True))
    op.add_column('service', sa.Column('enc_description', sa.Text(), nullable=True))
    
    # Копіюємо дані
    op.execute("UPDATE service SET enc_name = name, enc_description = description")
    
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.drop_column('name')
        batch_op.drop_column('description')

    # 3. СТРАТЕГІЯ ДЛЯ ТАБЛИЦІ APPOINTMENT
    op.add_column('appointment', sa.Column('enc_status', sa.Text(), nullable=True))
    op.add_column('appointment', sa.Column('enc_created_at', sa.Text(), nullable=True))
    
    # Копіюємо дані
    op.execute("UPDATE appointment SET enc_status = status, enc_created_at = created_at")
    
    with op.batch_alter_table('appointment', schema=None) as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('created_at')

def downgrade():
    # Логіка відкату (зворотне копіювання)
    with op.batch_alter_table('appointment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.Text(), nullable=True))
    op.execute("UPDATE appointment SET status = enc_status, created_at = enc_created_at")
    op.drop_column('appointment', 'enc_status')
    op.drop_column('appointment', 'enc_created_at')

    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('email', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.Text(), nullable=True))
    op.execute("UPDATE client SET name = enc_name, email = enc_email, phone = enc_phone")
    op.drop_column('client', 'enc_name')
    op.drop_column('client', 'enc_email')
    op.drop_column('client', 'enc_phone')

    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
    op.execute("UPDATE service SET name = enc_name, description = enc_description")
    op.drop_column('service', 'enc_name')
    op.drop_column('service', 'enc_description')