"""initial schema

Revision ID: 20260216_0001
Revises:
Create Date: 2026-02-16
"""

from alembic import op
import sqlalchemy as sa

revision = "20260216_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
        sa.Column("credits_balance", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_campaigns_owner_id", "campaigns", ["owner_id"], unique=False)

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("owner_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_assets_campaign_id", "assets", ["campaign_id"], unique=False)
    op.create_index("ix_assets_owner_id", "assets", ["owner_id"], unique=False)

    op.create_table(
        "asset_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("change_note", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_asset_versions_asset_id", "asset_versions", ["asset_id"], unique=False)

    op.create_table(
        "credit_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(120), nullable=False),
        sa.Column("reference_id", sa.String(120), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_credit_ledger_user_id", "credit_ledger", ["user_id"], unique=False)

    op.create_table(
        "usage_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("service", sa.String(80), nullable=False),
        sa.Column("endpoint", sa.String(120), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("cost_usd", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_usage_events_user_id", "usage_events", ["user_id"], unique=False)


    # ── Enable Row-Level Security on all tables ──────────────────────
    for table in ("users", "campaigns", "assets", "asset_versions", "credit_ledger", "usage_events"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    # Owner-scoped RLS policies
    op.execute("""
        CREATE POLICY users_self ON users FOR ALL
        USING (id = current_setting('app.user_id', true))
        WITH CHECK (id = current_setting('app.user_id', true))
    """)
    op.execute("""
        CREATE POLICY campaigns_owner ON campaigns FOR ALL
        USING (owner_id = current_setting('app.user_id', true))
        WITH CHECK (owner_id = current_setting('app.user_id', true))
    """)
    op.execute("""
        CREATE POLICY assets_owner ON assets FOR ALL
        USING (owner_id = current_setting('app.user_id', true))
        WITH CHECK (owner_id = current_setting('app.user_id', true))
    """)
    op.execute("""
        CREATE POLICY asset_versions_owner ON asset_versions FOR ALL
        USING (asset_id IN (SELECT id FROM assets WHERE owner_id = current_setting('app.user_id', true)))
    """)
    op.execute("""
        CREATE POLICY credit_ledger_owner ON credit_ledger FOR ALL
        USING (user_id = current_setting('app.user_id', true))
    """)
    op.execute("""
        CREATE POLICY usage_events_owner ON usage_events FOR ALL
        USING (user_id = current_setting('app.user_id', true))
    """)


def downgrade() -> None:
    # Drop RLS policies
    for table, policy in [
        ("users", "users_self"), ("campaigns", "campaigns_owner"),
        ("assets", "assets_owner"), ("asset_versions", "asset_versions_owner"),
        ("credit_ledger", "credit_ledger_owner"), ("usage_events", "usage_events_owner"),
    ]:
        op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
    for table in ("users", "campaigns", "assets", "asset_versions", "credit_ledger", "usage_events"):
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_usage_events_user_id", table_name="usage_events")
    op.drop_table("usage_events")
    op.drop_index("ix_credit_ledger_user_id", table_name="credit_ledger")
    op.drop_table("credit_ledger")
    op.drop_index("ix_asset_versions_asset_id", table_name="asset_versions")
    op.drop_table("asset_versions")
    op.drop_index("ix_assets_owner_id", table_name="assets")
    op.drop_index("ix_assets_campaign_id", table_name="assets")
    op.drop_table("assets")
    op.drop_index("ix_campaigns_owner_id", table_name="campaigns")
    op.drop_table("campaigns")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

