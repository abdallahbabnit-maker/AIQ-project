"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-11-15
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'agents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(120), unique=True, nullable=False, index=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('status', sa.String(30), default='active', index=True),
        sa.Column('capabilities', sa.JSON, default=list),
        sa.Column('max_concurrent_tasks', sa.Integer, default=5),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'skills',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(120), unique=True, nullable=False, index=True),
        sa.Column('description', sa.String(500), default=''),
    )

    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('action', sa.String(120), nullable=False),
        sa.Column('required_skills', sa.JSON, default=list),
        sa.Column('payload', sa.JSON, default=dict),
        sa.Column('risk', sa.String(20), default='low'),
        sa.Column('state', sa.String(30), default='queued', index=True),
        sa.Column('assigned_agent_id', sa.String(36), sa.ForeignKey('agents.id'), nullable=True, index=True),
        sa.Column('approval_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'approvals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), nullable=False, index=True),
        sa.Column('agent_id', sa.String(36), nullable=False, index=True),
        sa.Column('action', sa.String(120), nullable=False),
        sa.Column('risk', sa.String(20), nullable=False),
        sa.Column('payload', sa.JSON, default=dict),
        sa.Column('status', sa.String(30), default='pending', index=True),
        sa.Column('requested_by', sa.String(36), nullable=False),
        sa.Column('decided_by', sa.String(36), nullable=True),
        sa.Column('decision_note', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_type', sa.String(120), nullable=False, index=True),
        sa.Column('task_id', sa.String(36), nullable=True, index=True),
        sa.Column('agent_id', sa.String(36), nullable=True, index=True),
        sa.Column('actor_id', sa.String(36), nullable=True, index=True),
        sa.Column('detail', sa.JSON, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('approvals')
    op.drop_table('tasks')
    op.drop_table('skills')
    op.drop_table('agents')
