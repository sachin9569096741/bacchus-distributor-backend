from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dues.models import DueEntryType, DueLedger


def get_due_entry_by_id(
    db: Session,
    due_id: UUID,
) -> DueLedger | None:
    return db.scalar(
        select(DueLedger).where(DueLedger.id == due_id)
    )


def get_due_entries_by_seller(
    db: Session,
    seller_id: UUID,
) -> list[DueLedger]:
    stmt = (
        select(DueLedger)
        .where(DueLedger.seller_id == seller_id)
        .order_by(DueLedger.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_due_entries_by_distributor(
    db: Session,
    distributor_id: UUID,
) -> list[DueLedger]:
    stmt = (
        select(DueLedger)
        .where(DueLedger.distributor_id == distributor_id)
        .order_by(DueLedger.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_due_entries_by_type(
    db: Session,
    seller_id: UUID,
    entry_type: DueEntryType,
) -> list[DueLedger]:
    stmt = (
        select(DueLedger)
        .where(
            DueLedger.seller_id == seller_id,
            DueLedger.entry_type == entry_type,
        )
        .order_by(DueLedger.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_due_entry_by_reference(
    db: Session,
    reference_id: UUID,
    entry_type: DueEntryType | None = None,
) -> DueLedger | None:
    conditions = [DueLedger.reference_id == reference_id]

    if entry_type is not None:
        conditions.append(DueLedger.entry_type == entry_type)

    return db.scalar(
        select(DueLedger).where(*conditions)
    )


def get_due_entries_by_reference(
    db: Session,
    reference_id: UUID,
) -> list[DueLedger]:
    stmt = (
        select(DueLedger)
        .where(DueLedger.reference_id == reference_id)
        .order_by(DueLedger.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def create_due_entry(
    db: Session,
    due_entry: DueLedger,
) -> DueLedger:
    db.add(due_entry)
    db.flush()
    return due_entry

def get_all_due_entries(
    db: Session,
) -> list[DueLedger]:
    stmt = (
        select(DueLedger)
        .order_by(DueLedger.created_at.desc())
    )

    return list(db.scalars(stmt).all())
def save_due_entry(
    db: Session,
    due_entry: DueLedger,
) -> DueLedger:
    db.add(due_entry)
    db.flush()
    return due_entry