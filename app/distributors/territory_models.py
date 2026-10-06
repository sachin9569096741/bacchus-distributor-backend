import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DistributorZone(Base):
    __tablename__ = "distributor_zones"

    __table_args__ = (
        UniqueConstraint(
            "distributor_id",
            "zone_id",
            name="uq_distributor_zone",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    distributor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("zones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    distributor = relationship(
        "Distributor",
        back_populates="territory_zones",
    )

    zone = relationship("Zone")


class DistributorArea(Base):
    __tablename__ = "distributor_areas"

    __table_args__ = (
        UniqueConstraint(
            "distributor_id",
            "area_id",
            name="uq_distributor_area",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    distributor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("areas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    distributor = relationship(
        "Distributor",
        back_populates="territory_areas",
    )

    area = relationship("Area")