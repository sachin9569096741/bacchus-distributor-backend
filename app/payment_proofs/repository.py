from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.payment_proofs.models import PaymentProof, PaymentProofStatus


def get_payment_proof_by_id(
    db: Session,
    payment_proof_id: UUID,
) -> PaymentProof | None:
    return db.scalar(
        select(PaymentProof).where(PaymentProof.id == payment_proof_id)
    )


def get_payment_proof_by_code(
    db: Session,
    payment_proof_code: str,
) -> PaymentProof | None:
    return db.scalar(
        select(PaymentProof).where(
            PaymentProof.payment_proof_code == payment_proof_code
        )
    )


def get_payment_proof_by_payment_id(
    db: Session,
    payment_id: str,
) -> PaymentProof | None:
    return db.scalar(
        select(PaymentProof).where(
            PaymentProof.payment_id == payment_id
        )
    )


def get_payment_proofs_by_seller(
    db: Session,
    seller_id: UUID,
) -> list[PaymentProof]:
    stmt = (
        select(PaymentProof)
        .where(PaymentProof.seller_id == seller_id)
        .order_by(PaymentProof.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_payment_proofs_by_salesperson(
    db: Session,
    salesperson_id: UUID,
) -> list[PaymentProof]:
    stmt = (
        select(PaymentProof)
        .where(PaymentProof.salesperson_id == salesperson_id)
        .order_by(PaymentProof.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_payment_proofs_by_distributor(
    db: Session,
    distributor_id: UUID,
) -> list[PaymentProof]:
    stmt = (
        select(PaymentProof)
        .where(PaymentProof.distributor_id == distributor_id)
        .order_by(PaymentProof.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_pending_payment_proofs_by_distributor(
    db: Session,
    distributor_id: UUID,
) -> list[PaymentProof]:
    stmt = (
        select(PaymentProof)
        .where(
            PaymentProof.distributor_id == distributor_id,
            PaymentProof.status == PaymentProofStatus.PENDING,
        )
        .order_by(PaymentProof.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_payment_proofs_by_status(
    db: Session,
    status: PaymentProofStatus,
) -> list[PaymentProof]:
    stmt = (
        select(PaymentProof)
        .where(PaymentProof.status == status)
        .order_by(PaymentProof.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_all_payment_proofs(
    db: Session,
) -> list[PaymentProof]:
    stmt = select(PaymentProof).order_by(
        PaymentProof.created_at.desc()
    )
    return list(db.scalars(stmt).all())


def create_payment_proof(
    db: Session,
    payment_proof: PaymentProof,
) -> PaymentProof:
    db.add(payment_proof)
    db.flush()
    return payment_proof


def save_payment_proof(
    db: Session,
    payment_proof: PaymentProof,
) -> PaymentProof:
    db.add(payment_proof)
    db.flush()
    return payment_proof