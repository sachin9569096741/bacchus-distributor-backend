from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.inventory.service import (
    InventoryService,
    InventoryServiceError,
)
from app.dues.service import DueService
from app.sales.models import Sale, SaleItem
from app.sales.repository import (
    create_sale,
    create_sale_item,
    get_sale_by_id,
    get_sale_by_number,
    get_sales_by_distributor,
    get_sales_by_salesperson,
    get_sales_by_seller,
    get_sale_items,
)


MONEY_QUANT = Decimal("0.01")


class SaleServiceError(Exception):
    """Base exception for sales business errors."""


class SaleNotFoundError(SaleServiceError):
    pass


class SaleAlreadyExistsError(SaleServiceError):
    pass


class InvalidSaleError(SaleServiceError):
    pass


class SaleScopeError(SaleServiceError):
    pass


class SaleInventoryError(SaleServiceError):
    pass


class SaleService:

    # ========================================================
    # MONEY
    # ========================================================

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(
            MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )

    # ========================================================
    # SALE NUMBER
    # ========================================================

    @staticmethod
    def _generate_sale_number(
        distributor_code: str,
    ) -> str:
        return (
            f"{distributor_code}-SALE-"
            f"{uuid4().hex[:8].upper()}"
        )

    # ========================================================
    # DISTRIBUTOR
    # ========================================================

    @staticmethod
    def _get_distributor(
        db: Session,
        distributor_id: UUID,
    ):
        from app.distributors.repository import (
            get_distributor_by_id,
        )

        distributor = get_distributor_by_id(
            db=db,
            distributor_id=distributor_id,
        )

        if distributor is None:
            raise InvalidSaleError(
                "Distributor not found."
            )

        if not distributor.is_active:
            raise InvalidSaleError(
                "Distributor is inactive."
            )

        return distributor

    # ========================================================
    # SALESPERSON
    # ========================================================

    @staticmethod
    def _get_salesperson(
        db: Session,
        salesperson_id: UUID,
    ):
        from app.salespersons.repository import (
            get_salesperson_by_id,
        )

        salesperson = get_salesperson_by_id(
            db=db,
            salesperson_id=salesperson_id,
        )

        if salesperson is None:
            raise InvalidSaleError(
                "Salesperson not found."
            )

        if not salesperson.is_active:
            raise InvalidSaleError(
                "Salesperson is inactive."
            )

        return salesperson

    # ========================================================
    # SELLER
    # ========================================================

    @staticmethod
    def _get_seller(
        db: Session,
        seller_id: UUID,
    ):
        from app.sellers.repository import (
            get_seller_by_id,
        )

        seller = get_seller_by_id(
            db=db,
            seller_id=seller_id,
        )

        if seller is None:
            raise InvalidSaleError(
                "Seller not found."
            )

        if not seller.is_active:
            raise InvalidSaleError(
                "Seller is inactive."
            )

        return seller

    # ========================================================
    # RELATIONSHIP VALIDATION
    # ========================================================

    @staticmethod
    def _validate_sales_relationship(
        *,
        seller,
        salesperson,
        distributor,
    ) -> None:

        if seller.distributor_id != distributor.id:
            raise SaleScopeError(
                "Seller does not belong to this distributor."
            )

        if seller.salesperson_id != salesperson.id:
            raise SaleScopeError(
                "Seller is not assigned to this salesperson."
            )

        if salesperson.distributor_id != distributor.id:
            raise SaleScopeError(
                "Salesperson does not belong to this distributor."
            )

        if (
            seller.state_id != distributor.state_id
            or seller.zone_id != distributor.zone_id
            or seller.area_id != distributor.area_id
        ):
            raise SaleScopeError(
                "Seller territory does not match the distributor."
            )

        if (
            salesperson.state_id != distributor.state_id
            or salesperson.zone_id != distributor.zone_id
            or salesperson.area_id != distributor.area_id
        ):
            raise SaleScopeError(
                "Salesperson territory does not match the distributor."
            )

    # ========================================================
    # PRODUCT VALIDATION
    # ========================================================

    @staticmethod
    def _get_product(
        db: Session,
        product_id: UUID,
    ):
        from app.products.repository import (
            get_product_by_id,
        )

        product = get_product_by_id(
            db=db,
            product_id=product_id,
        )

        if product is None:
            raise InvalidSaleError(
                "Product not found."
            )

        if not product.is_active:
            raise InvalidSaleError(
                "Product is inactive."
            )

        return product

    # ========================================================
    # VARIANT VALIDATION
    # ========================================================

    @staticmethod
    def _validate_variant(
        db: Session,
        *,
        product_id: UUID,
        variant_id: UUID | None,
    ) -> None:

        if variant_id is None:
            return

        from app.products.repository import (
            get_variant_by_id,
        )

        variant = get_variant_by_id(
            db=db,
            variant_id=variant_id,
        )

        if variant is None:
            raise InvalidSaleError(
                "Product variant not found."
            )

        if not variant.is_active:
            raise InvalidSaleError(
                "Product variant is inactive."
            )

        if variant.product_id != product_id:
            raise InvalidSaleError(
                "Variant does not belong to the selected product."
            )

    # ========================================================
    # CREATE SALE
    # ========================================================

    @staticmethod
    def create_sale(
        db: Session,
        *,
        seller_id: UUID,
        salesperson_id: UUID,
        distributor_id: UUID,
        sale_date: date,
        items: list[dict],
        created_by: UUID,
        remarks: str | None = None,
    ) -> Sale:

        if not items:
            raise InvalidSaleError(
                "A sale must contain at least one item."
            )

        # ----------------------------------------------------
        # Validate main entities
        # ----------------------------------------------------

        distributor = SaleService._get_distributor(
            db=db,
            distributor_id=distributor_id,
        )

        salesperson = SaleService._get_salesperson(
            db=db,
            salesperson_id=salesperson_id,
        )

        seller = SaleService._get_seller(
            db=db,
            seller_id=seller_id,
        )

        SaleService._validate_sales_relationship(
            seller=seller,
            salesperson=salesperson,
            distributor=distributor,
        )

        # ----------------------------------------------------
        # Prevent duplicate product + variant combinations
        # ----------------------------------------------------

        combinations: set[
            tuple[UUID, UUID | None]
        ] = set()

        prepared_items: list[dict] = []

        total_amount = Decimal("0.00")
        # ----------------------------------------------------
        # Validate and calculate all items BEFORE changing
        # inventory.
        # ----------------------------------------------------

        for item in items:

            product_id = item["product_id"]
            variant_id = item.get("variant_id")
            quantity = item["quantity"]
            selling_price = item["selling_price"]

            if quantity <= 0:
                raise InvalidSaleError(
                    "Sale quantity must be greater than zero."
                )

            if selling_price < 0:
                raise InvalidSaleError(
                    "Selling price cannot be negative."
                )

            SaleService._get_product(
                db=db,
                product_id=product_id,
            )

            SaleService._validate_variant(
                db=db,
                product_id=product_id,
                variant_id=variant_id,
            )

            combination = (
                product_id,
                variant_id,
            )

            if combination in combinations:
                raise InvalidSaleError(
                    "The same product/variant cannot appear "
                    "more than once in a sale."
                )

            combinations.add(combination)

            selling_price = SaleService._money(
                selling_price
            )

            line_total = SaleService._money(
                quantity * selling_price
            )

            total_amount += line_total

            prepared_items.append(
                {
                    "product_id": product_id,
                    "variant_id": variant_id,
                    "quantity": quantity,
                    "selling_price": selling_price,
                    "line_total": line_total,
                }
            )

        total_amount = SaleService._money(
            total_amount
        )

        # ----------------------------------------------------
        # Generate sale number
        # ----------------------------------------------------

        sale_number = SaleService._generate_sale_number(
            distributor_code=distributor.distributor_code,
        )

        # ----------------------------------------------------
        # Create sale
        # ----------------------------------------------------

        sale = Sale(
            id=uuid4(),
            sale_number=sale_number,
            seller_id=seller_id,
            salesperson_id=salesperson_id,
            distributor_id=distributor_id,
            sale_date=sale_date,
            total_amount=total_amount,
            remarks=remarks,
            created_by=created_by,
        )

        create_sale(
            db=db,
            sale=sale,
        )

        # ----------------------------------------------------
        # Deduct inventory + create sale items
        # ----------------------------------------------------

        try:

            for item in prepared_items:

                # Salesperson stock is reduced for the sale.
                InventoryService.deduct_sale_stock(
                    db=db,
                    distributor_id=distributor_id,
                    salesperson_id=salesperson_id,
                    product_id=item["product_id"],
                    variant_id=item["variant_id"],
                    quantity=item["quantity"],
                    performed_by=created_by,
                    reference_id=sale.id,
                    remarks=(
                        f"Sale {sale.sale_number}"
                    ),
                )

                sale_item = SaleItem(
                    id=uuid4(),
                    sale_id=sale.id,
                    product_id=item["product_id"],
                    variant_id=item["variant_id"],
                    quantity=item["quantity"],
                    selling_price=item["selling_price"],
                    line_total=item["line_total"],
                )

                create_sale_item(
                    db=db,
                    sale_item=sale_item,
                )

        except InventoryServiceError as exc:

            raise SaleInventoryError(
                str(exc)
            ) from exc

        db.flush()

        # ----------------------------------------------------
        # Create seller due entry
        # ----------------------------------------------------
        # This stays in the same transaction as the sale and
        # inventory changes. If due creation fails, the caller
        # can roll back the complete transaction.
        DueService.record_credit_sale(
            db=db,
            seller_id=seller.id,
            distributor_id=distributor.id,
            sale_id=sale.id,
            amount=total_amount,
            created_by=created_by,
        )

        db.flush()

        return sale

    # ========================================================
    # GET SALE
    # ========================================================

    @staticmethod
    def get_sale(
        db: Session,
        sale_id: UUID,
    ) -> Sale:

        sale = get_sale_by_id(
            db=db,
            sale_id=sale_id,
        )

        if sale is None:
            raise SaleNotFoundError(
                "Sale not found."
            )

        return sale

    # ========================================================
    # GET BY SALE NUMBER
    # ========================================================

    @staticmethod
    def get_sale_by_number(
        db: Session,
        sale_number: str,
    ) -> Sale:

        sale = get_sale_by_number(
            db=db,
            sale_number=sale_number,
        )

        if sale is None:
            raise SaleNotFoundError(
                "Sale not found."
            )

        return sale

    # ========================================================
    # SALE ITEMS
    # ========================================================

    @staticmethod
    def get_sale_items(
        db: Session,
        sale_id: UUID,
    ) -> list[SaleItem]:

        SaleService.get_sale(
            db=db,
            sale_id=sale_id,
        )

        return get_sale_items(
            db=db,
            sale_id=sale_id,
        )

    # ========================================================
    # LIST SALES
    # ========================================================

    @staticmethod
    def list_distributor_sales(
        db: Session,
        distributor_id: UUID,
    ) -> list[Sale]:

        return get_sales_by_distributor(
            db=db,
            distributor_id=distributor_id,
        )

    @staticmethod
    def list_salesperson_sales(
        db: Session,
        salesperson_id: UUID,
    ) -> list[Sale]:

        return get_sales_by_salesperson(
            db=db,
            salesperson_id=salesperson_id,
        )

    @staticmethod
    def list_seller_sales(
        db: Session,
        seller_id: UUID,
    ) -> list[Sale]:

        return get_sales_by_seller(
            db=db,
            seller_id=seller_id,
        )