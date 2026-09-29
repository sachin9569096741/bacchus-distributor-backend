from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    AdminAnalyticsResponse,
    DistributorAnalyticsResponse,
    SellerAnalyticsResponse,
    SalesTrendItem,
    SellerPerformanceAnalytics,
    TopDistributorAnalytics,
    TopGeographyAnalytics,
    TopProductAnalytics,
)
from app.distributors.models import Distributor
from app.dues.models import DueEntryType, DueLedger
from app.geography.models import Area, State, Zone
from app.inventory.models import Inventory
from app.payment_proofs.models import PaymentProof, PaymentProofStatus
from app.products.models import Product
from app.sales.models import Sale, SaleItem
from app.salespersons.models import Salesperson
from app.sellers.models import Seller
from app.stock_requests.models import (
    StockRequest,
    StockRequestStatus,
)


class AnalyticsService:

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _decimal(value) -> Decimal:
        return value if value is not None else Decimal("0")

    @staticmethod
    def _outstanding_for_sellers(
        db: Session,
        seller_ids: list[UUID],
    ) -> Decimal:

        if not seller_ids:
            return Decimal("0")

        result = db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                DueLedger.entry_type
                                == DueEntryType.CREDIT_SALE,
                                DueLedger.amount,
                            ),
                            (
                                DueLedger.entry_type
                                == DueEntryType.VERIFIED_PAYMENT,
                                -DueLedger.amount,
                            ),
                            else_=DueLedger.amount,
                        )
                    ),
                    0,
                )
            ).where(
                DueLedger.seller_id.in_(seller_ids)
            )
        )

        return AnalyticsService._decimal(result)

    @staticmethod
    def _verified_payments(
        db: Session,
        seller_ids: list[UUID],
    ) -> Decimal:

        if not seller_ids:
            return Decimal("0")

        result = db.scalar(
            select(
                func.coalesce(
                    func.sum(DueLedger.amount),
                    0,
                )
            ).where(
                DueLedger.seller_id.in_(seller_ids),
                DueLedger.entry_type
                == DueEntryType.VERIFIED_PAYMENT,
            )
        )

        return AnalyticsService._decimal(result)

    # ============================================================
    # SALES TREND
    # ============================================================

    @staticmethod
    def _sales_trend(
        db: Session,
        seller_ids: list[UUID] | None = None,
        distributor_id: UUID | None = None,
    ) -> list[SalesTrendItem]:

        stmt = (
            select(
                Sale.sale_date.label("date"),
                func.count(Sale.id).label("sales_count"),
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).label("sales_amount"),
            )
            .group_by(Sale.sale_date)
            .order_by(Sale.sale_date)
        )

        if seller_ids is not None:

            if not seller_ids:
                return []

            stmt = stmt.where(
                Sale.seller_id.in_(seller_ids)
            )

        if distributor_id is not None:
            stmt = stmt.where(
                Sale.distributor_id == distributor_id
            )

        rows = db.execute(stmt).all()

        return [
            SalesTrendItem(
                date=row.date,
                sales_count=row.sales_count,
                sales_amount=AnalyticsService._decimal(
                    row.sales_amount
                ),
            )
            for row in rows
        ]

    # ============================================================
    # TOP PRODUCTS
    # ============================================================

    @staticmethod
    def _top_products(
        db: Session,
        seller_ids: list[UUID] | None = None,
        distributor_id: UUID | None = None,
    ) -> list[TopProductAnalytics]:

        stmt = (
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                func.coalesce(
                    func.sum(SaleItem.quantity),
                    0,
                ).label("quantity_sold"),
                func.coalesce(
                    func.sum(SaleItem.line_total),
                    0,
                ).label("sales_amount"),
            )
            .join(
                SaleItem,
                SaleItem.product_id == Product.id,
            )
            .join(
                Sale,
                Sale.id == SaleItem.sale_id,
            )
            .group_by(
                Product.id,
                Product.name,
            )
            .order_by(
                func.coalesce(
                    func.sum(SaleItem.quantity),
                    0,
                ).desc()
            )
            .limit(10)
        )

        if seller_ids is not None:

            if not seller_ids:
                return []

            stmt = stmt.where(
                Sale.seller_id.in_(seller_ids)
            )

        if distributor_id is not None:
            stmt = stmt.where(
                Sale.distributor_id == distributor_id
            )

        rows = db.execute(stmt).all()

        return [
            TopProductAnalytics(
                product_id=row.product_id,
                product_name=row.product_name,
                quantity_sold=AnalyticsService._decimal(
                    row.quantity_sold
                ),
                sales_amount=AnalyticsService._decimal(
                    row.sales_amount
                ),
            )
            for row in rows
        ]

    # ============================================================
    # TOP STATES
    # ============================================================

    @staticmethod
    def _top_states(
        db: Session,
    ) -> list[TopGeographyAnalytics]:

        rows = db.execute(
            select(
                State.id.label("id"),
                State.name.label("name"),
                func.count(Sale.id).label("sales_count"),
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).label("sales_amount"),
            )
            .outerjoin(
                Distributor,
                Distributor.state_id == State.id,
            )
            .outerjoin(
                Sale,
                Sale.distributor_id == Distributor.id,
            )
            .where(
                State.is_active.is_(True)
            )
            .group_by(
                State.id,
                State.name,
            )
            .order_by(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).desc()
            )
            .limit(10)
        ).all()

        return [
            TopGeographyAnalytics(
                id=row.id,
                name=row.name,
                sales_count=row.sales_count,
                sales_amount=AnalyticsService._decimal(
                    row.sales_amount
                ),
            )
            for row in rows
        ]

    # ============================================================
    # TOP ZONES
    # ============================================================

    @staticmethod
    def _top_zones(
        db: Session,
    ) -> list[TopGeographyAnalytics]:

        rows = db.execute(
            select(
                Zone.id.label("id"),
                Zone.name.label("name"),
                func.count(Sale.id).label("sales_count"),
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).label("sales_amount"),
            )
            .outerjoin(
                Distributor,
                Distributor.zone_id == Zone.id,
            )
            .outerjoin(
                Sale,
                Sale.distributor_id == Distributor.id,
            )
            .where(
                Zone.is_active.is_(True)
            )
            .group_by(
                Zone.id,
                Zone.name,
            )
            .order_by(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).desc()
            )
            .limit(10)
        ).all()

        return [
            TopGeographyAnalytics(
                id=row.id,
                name=row.name,
                sales_count=row.sales_count,
                sales_amount=AnalyticsService._decimal(
                    row.sales_amount
                ),
            )
            for row in rows
        ]

    # ============================================================
    # TOP AREAS
    # ============================================================

    @staticmethod
    def _top_areas(
        db: Session,
    ) -> list[TopGeographyAnalytics]:

        rows = db.execute(
            select(
                Area.id.label("id"),
                Area.name.label("name"),
                func.count(Sale.id).label("sales_count"),
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).label("sales_amount"),
            )
            .outerjoin(
                Distributor,
                Distributor.area_id == Area.id,
            )
            .outerjoin(
                Sale,
                Sale.distributor_id == Distributor.id,
            )
            .where(
                Area.is_active.is_(True)
            )
            .group_by(
                Area.id,
                Area.name,
            )
            .order_by(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).desc()
            )
            .limit(10)
        ).all()

        return [
            TopGeographyAnalytics(
                id=row.id,
                name=row.name,
                sales_count=row.sales_count,
                sales_amount=AnalyticsService._decimal(
                    row.sales_amount
                ),
            )
            for row in rows
        ]

    # ============================================================
    # ADMIN ANALYTICS
    # ============================================================

    @staticmethod
    def get_admin_analytics(
        db: Session,
    ) -> AdminAnalyticsResponse:

        # -----------------------------
        # Geography
        # -----------------------------

        total_states = db.scalar(
            select(func.count(State.id)).where(
                State.is_active.is_(True)
            )
        ) or 0

        total_zones = db.scalar(
            select(func.count(Zone.id)).where(
                Zone.is_active.is_(True)
            )
        ) or 0

        total_areas = db.scalar(
            select(func.count(Area.id)).where(
                Area.is_active.is_(True)
            )
        ) or 0

        # -----------------------------
        # Network
        # -----------------------------

        total_distributors = db.scalar(
            select(func.count(Distributor.id)).where(
                Distributor.is_active.is_(True)
            )
        ) or 0

        total_salespersons = db.scalar(
            select(func.count(Salesperson.id)).where(
                Salesperson.is_active.is_(True)
            )
        ) or 0

        total_sellers = db.scalar(
            select(func.count(Seller.id)).where(
                Seller.is_active.is_(True)
            )
        ) or 0

        # -----------------------------
        # Sales
        # -----------------------------

        total_sales = db.scalar(
            select(func.count(Sale.id))
        ) or 0

        total_sales_amount = db.scalar(
            select(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                )
            )
        )

        # -----------------------------
        # Due
        # -----------------------------

        total_outstanding_due = db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                DueLedger.entry_type
                                == DueEntryType.CREDIT_SALE,
                                DueLedger.amount,
                            ),
                            (
                                DueLedger.entry_type
                                == DueEntryType.VERIFIED_PAYMENT,
                                -DueLedger.amount,
                            ),
                            else_=DueLedger.amount,
                        )
                    ),
                    0,
                )
            )
        )

        total_verified_payments = db.scalar(
            select(
                func.coalesce(
                    func.sum(DueLedger.amount),
                    0,
                )
            ).where(
                DueLedger.entry_type
                == DueEntryType.VERIFIED_PAYMENT
            )
        )

        # -----------------------------
        # Pending
        # -----------------------------

        pending_payment_proofs = db.scalar(
            select(func.count(PaymentProof.id)).where(
                PaymentProof.status
                == PaymentProofStatus.PENDING
            )
        ) or 0

        pending_stock_requests = db.scalar(
            select(func.count(StockRequest.id)).where(
                StockRequest.status
                == StockRequestStatus.PENDING
            )
        ) or 0

        # -----------------------------
        # Inventory
        # -----------------------------

        total_inventory_quantity = db.scalar(
            select(
                func.coalesce(
                    func.sum(Inventory.quantity),
                    0,
                )
            )
        )

        # -----------------------------
        # Top distributors
        # -----------------------------

        distributor_rows = db.execute(
            select(
                Distributor.id.label("distributor_id"),
                Distributor.business_name.label(
                    "distributor_name"
                ),
                func.count(Sale.id).label("sales_count"),
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).label("sales_amount"),
            )
            .outerjoin(
                Sale,
                Sale.distributor_id == Distributor.id,
            )
            .where(
                Distributor.is_active.is_(True)
            )
            .group_by(
                Distributor.id,
                Distributor.business_name,
            )
            .order_by(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).desc()
            )
            .limit(10)
        ).all()

        top_distributors = [
            TopDistributorAnalytics(
                distributor_id=row.distributor_id,
                distributor_name=row.distributor_name,
                sales_count=row.sales_count,
                sales_amount=AnalyticsService._decimal(
                    row.sales_amount
                ),
            )
            for row in distributor_rows
        ]

        return AdminAnalyticsResponse(
            total_states=total_states,
            total_zones=total_zones,
            total_areas=total_areas,

            total_distributors=total_distributors,
            total_salespersons=total_salespersons,
            total_sellers=total_sellers,

            total_sales=total_sales,
            total_sales_amount=AnalyticsService._decimal(
                total_sales_amount
            ),

            total_outstanding_due=AnalyticsService._decimal(
                total_outstanding_due
            ),
            total_verified_payments=AnalyticsService._decimal(
                total_verified_payments
            ),

            pending_payment_proofs=pending_payment_proofs,
            pending_stock_requests=pending_stock_requests,

            total_inventory_quantity=AnalyticsService._decimal(
                total_inventory_quantity
            ),

            top_products=AnalyticsService._top_products(db),
            top_distributors=top_distributors,
            top_states=AnalyticsService._top_states(db),
            top_zones=AnalyticsService._top_zones(db),
            top_areas=AnalyticsService._top_areas(db),

            sales_trend=AnalyticsService._sales_trend(db),
        )

    # ============================================================
    # DISTRIBUTOR ANALYTICS
    # ============================================================

    @staticmethod
    def get_distributor_analytics(
        db: Session,
        distributor_id: UUID,
    ) -> DistributorAnalyticsResponse:

        distributor = db.scalar(
            select(Distributor).where(
                Distributor.id == distributor_id
            )
        )

        if distributor is None:
            raise ValueError("Distributor not found")

        seller_ids = list(
            db.scalars(
                select(Seller.id).where(
                    Seller.distributor_id == distributor_id,
                    Seller.is_active.is_(True),
                )
            ).all()
        )

        total_salespersons = db.scalar(
            select(func.count(Salesperson.id)).where(
                Salesperson.distributor_id == distributor_id,
                Salesperson.is_active.is_(True),
            )
        ) or 0

        total_sellers = len(seller_ids)

        total_sales = db.scalar(
            select(func.count(Sale.id)).where(
                Sale.distributor_id == distributor_id
            )
        ) or 0

        total_sales_amount = db.scalar(
            select(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                )
            ).where(
                Sale.distributor_id == distributor_id
            )
        )

        outstanding_due = (
            AnalyticsService._outstanding_for_sellers(
                db,
                seller_ids,
            )
        )

        verified_payments = (
            AnalyticsService._verified_payments(
                db,
                seller_ids,
            )
        )

        pending_payment_proofs = db.scalar(
            select(func.count(PaymentProof.id)).where(
                PaymentProof.distributor_id == distributor_id,
                PaymentProof.status
                == PaymentProofStatus.PENDING,
            )
        ) or 0

        pending_stock_requests = db.scalar(
            select(func.count(StockRequest.id)).where(
                StockRequest.distributor_id == distributor_id,
                StockRequest.status
                == StockRequestStatus.PENDING,
            )
        ) or 0

        total_inventory_quantity = db.scalar(
            select(
                func.coalesce(
                    func.sum(Inventory.quantity),
                    0,
                )
            ).where(
                Inventory.distributor_id == distributor_id
            )
        )

        seller_rows = db.execute(
            select(
                Seller.id.label("seller_id"),
                Seller.business_name.label("seller_name"),
                func.count(Sale.id).label("sales_count"),
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).label("sales_amount"),
            )
            .outerjoin(
                Sale,
                Sale.seller_id == Seller.id,
            )
            .where(
                Seller.distributor_id == distributor_id
            )
            .group_by(
                Seller.id,
                Seller.business_name,
            )
            .order_by(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                ).desc()
            )
            .limit(10)
        ).all()

        seller_performance = []

        for row in seller_rows:
            due = AnalyticsService._outstanding_for_sellers(
                db,
                [row.seller_id],
            )

            seller_performance.append(
                SellerPerformanceAnalytics(
                    seller_id=row.seller_id,
                    seller_name=row.seller_name,
                    sales_count=row.sales_count,
                    sales_amount=AnalyticsService._decimal(
                        row.sales_amount
                    ),
                    outstanding_due=due,
                )
            )

        return DistributorAnalyticsResponse(
            distributor_id=distributor.id,
            distributor_name=distributor.business_name,

            total_salespersons=total_salespersons,
            total_sellers=total_sellers,

            total_sales=total_sales,
            total_sales_amount=AnalyticsService._decimal(
                total_sales_amount
            ),

            outstanding_due=outstanding_due,
            verified_payments=verified_payments,

            pending_payment_proofs=pending_payment_proofs,
            pending_stock_requests=pending_stock_requests,

            total_inventory_quantity=AnalyticsService._decimal(
                total_inventory_quantity
            ),

            top_products=AnalyticsService._top_products(
                db,
                distributor_id=distributor_id,
            ),

            seller_performance=seller_performance,

            sales_trend=AnalyticsService._sales_trend(
                db,
                distributor_id=distributor_id,
            ),
        )

    # ============================================================
    # SELLER ANALYTICS
    # ============================================================

    @staticmethod
    def get_seller_analytics(
        db: Session,
        seller_id: UUID,
    ) -> SellerAnalyticsResponse:

        seller = db.scalar(
            select(Seller).where(
                Seller.id == seller_id
            )
        )

        if seller is None:
            raise ValueError("Seller not found")

        total_sales = db.scalar(
            select(func.count(Sale.id)).where(
                Sale.seller_id == seller_id
            )
        ) or 0

        total_sales_amount = db.scalar(
            select(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                )
            ).where(
                Sale.seller_id == seller_id
            )
        )

        outstanding_due = (
            AnalyticsService._outstanding_for_sellers(
                db,
                [seller_id],
            )
        )

        verified_payments = (
            AnalyticsService._verified_payments(
                db,
                [seller_id],
            )
        )

        total_payment_proofs = db.scalar(
            select(func.count(PaymentProof.id)).where(
                PaymentProof.seller_id == seller_id
            )
        ) or 0

        pending_payment_proofs = db.scalar(
            select(func.count(PaymentProof.id)).where(
                PaymentProof.seller_id == seller_id,
                PaymentProof.status
                == PaymentProofStatus.PENDING,
            )
        ) or 0

        total_products = db.scalar(
            select(
                func.count(
                    func.distinct(
                        SaleItem.product_id
                    )
                )
            )
            .join(
                Sale,
                Sale.id == SaleItem.sale_id,
            )
            .where(
                Sale.seller_id == seller_id
            )
        ) or 0

        total_quantity = db.scalar(
            select(
                func.coalesce(
                    func.sum(SaleItem.quantity),
                    0,
                )
            )
            .join(
                Sale,
                Sale.id == SaleItem.sale_id,
            )
            .where(
                Sale.seller_id == seller_id
            )
        )

        return SellerAnalyticsResponse(
            seller_id=seller.id,
            seller_name=seller.business_name,

            total_sales=total_sales,
            total_sales_amount=AnalyticsService._decimal(
                total_sales_amount
            ),

            outstanding_due=outstanding_due,
            verified_payments=verified_payments,

            total_payment_proofs=total_payment_proofs,
            pending_payment_proofs=pending_payment_proofs,

            total_products=total_products,
            total_quantity=AnalyticsService._decimal(
                total_quantity
            ),

            sales_trend=AnalyticsService._sales_trend(
                db,
                seller_ids=[seller_id],
            ),
        )

        # 76150169-5548-410f-942e-c4b47725908d