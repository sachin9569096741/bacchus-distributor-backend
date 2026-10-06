import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Distributor(Base):
    __tablename__ = "distributors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    distributor_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    business_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    owner_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    mobile: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("states.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("zones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("areas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    gst_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    license_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    credit_limit: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    state = relationship("State")
    zone = relationship("Zone")
    area = relationship("Area")
    user = relationship("User")

    territory_zones = relationship(
        "DistributorZone",
        back_populates="distributor",
        cascade="all, delete-orphan",
    )

    territory_areas = relationship(
        "DistributorArea",
        back_populates="distributor",
        cascade="all, delete-orphan",
    )


    @property
    def zone_ids(self) -> list[uuid.UUID]:
        return [
            mapping.zone_id
            for mapping in self.territory_zones
        ]

    @property
    def area_ids(self) -> list[uuid.UUID]:
        return [
            mapping.area_id
            for mapping in self.territory_areas
        ]