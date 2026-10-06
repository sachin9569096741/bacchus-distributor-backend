"""add distributor territory mappings

Revision ID: 44bb1b0984ca
Revises: fa41c0f89e71
Create Date: 2026-10-05 15:40:59.290088

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "44bb1b0984ca"
down_revision: Union[str, Sequence[str], None] = "fa41c0f89e71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ============================================================
    # DISTRIBUTOR AREAS
    # ============================================================

    op.create_table(
        "distributor_areas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("distributor_id", sa.UUID(), nullable=False),
        sa.Column("area_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["distributor_id"],
            ["distributors.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "distributor_id",
            "area_id",
            name="uq_distributor_area",
        ),
    )

    op.create_index(
        op.f("ix_distributor_areas_area_id"),
        "distributor_areas",
        ["area_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_distributor_areas_distributor_id"),
        "distributor_areas",
        ["distributor_id"],
        unique=False,
    )

    # ============================================================
    # DISTRIBUTOR ZONES
    # ============================================================

    op.create_table(
        "distributor_zones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("distributor_id", sa.UUID(), nullable=False),
        sa.Column("zone_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["distributor_id"],
            ["distributors.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["zone_id"],
            ["zones.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "distributor_id",
            "zone_id",
            name="uq_distributor_zone",
        ),
    )

    op.create_index(
        op.f("ix_distributor_zones_distributor_id"),
        "distributor_zones",
        ["distributor_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_distributor_zones_zone_id"),
        "distributor_zones",
        ["zone_id"],
        unique=False,
    )

    # ============================================================
    # BACKFILL EXISTING DISTRIBUTOR TERRITORIES
    #
    # Existing distributors currently have:
    #   distributors.zone_id
    #   distributors.area_id
    #
    # Copy those values into the new mapping tables.
    # ============================================================

    bind = op.get_bind()

    distributors = bind.execute(
        sa.text(
            """
            SELECT id, zone_id, area_id
            FROM distributors
            WHERE zone_id IS NOT NULL
               OR area_id IS NOT NULL
            """
        )
    ).mappings().all()

    # ------------------------------------------------------------
    # Backfill distributor_zones
    # ------------------------------------------------------------

    zone_rows = [
        {
            "id": uuid.uuid4(),
            "distributor_id": row["id"],
            "zone_id": row["zone_id"],
        }
        for row in distributors
        if row["zone_id"] is not None
    ]

    if zone_rows:
        distributor_zones = sa.table(
            "distributor_zones",
            sa.column("id", sa.UUID()),
            sa.column("distributor_id", sa.UUID()),
            sa.column("zone_id", sa.UUID()),
        )

        bind.execute(
            distributor_zones.insert(),
            zone_rows,
        )

    # ------------------------------------------------------------
    # Backfill distributor_areas
    # ------------------------------------------------------------

    area_rows = [
        {
            "id": uuid.uuid4(),
            "distributor_id": row["id"],
            "area_id": row["area_id"],
        }
        for row in distributors
        if row["area_id"] is not None
    ]

    if area_rows:
        distributor_areas = sa.table(
            "distributor_areas",
            sa.column("id", sa.UUID()),
            sa.column("distributor_id", sa.UUID()),
            sa.column("area_id", sa.UUID()),
        )

        bind.execute(
            distributor_areas.insert(),
            area_rows,
        )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_distributor_zones_zone_id"),
        table_name="distributor_zones",
    )

    op.drop_index(
        op.f("ix_distributor_zones_distributor_id"),
        table_name="distributor_zones",
    )

    op.drop_table("distributor_zones")

    op.drop_index(
        op.f("ix_distributor_areas_distributor_id"),
        table_name="distributor_areas",
    )

    op.drop_index(
        op.f("ix_distributor_areas_area_id"),
        table_name="distributor_areas",
    )

    op.drop_table("distributor_areas")