from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SalesTrendItem(BaseModel):
    date: date
    sales_count: int
    sales_amount: Decimal


class TopProductAnalytics(BaseModel):
    product_id: UUID
    product_name: str
    quantity_sold: Decimal
    sales_amount: Decimal


class TopDistributorAnalytics(BaseModel):
    distributor_id: UUID
    distributor_name: str
    sales_count: int
    sales_amount: Decimal


class TopGeographyAnalytics(BaseModel):
    id: UUID
    name: str
    sales_count: int
    sales_amount: Decimal


class SellerPerformanceAnalytics(BaseModel):
    seller_id: UUID
    seller_name: str
    sales_count: int
    sales_amount: Decimal
    outstanding_due: Decimal


class AdminAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Geography
    total_states: int
    total_zones: int
    total_areas: int

    # Network
    total_distributors: int
    total_salespersons: int
    total_sellers: int

    # Sales
    total_sales: int
    total_sales_amount: Decimal

    # Finance
    total_outstanding_due: Decimal
    total_verified_payments: Decimal

    # Pending operations
    pending_payment_proofs: int
    pending_stock_requests: int

    # Inventory
    total_inventory_quantity: Decimal

    # Rankings
    top_products: list[TopProductAnalytics]
    top_distributors: list[TopDistributorAnalytics]
    top_states: list[TopGeographyAnalytics]
    top_zones: list[TopGeographyAnalytics]
    top_areas: list[TopGeographyAnalytics]

    # Trend
    sales_trend: list[SalesTrendItem]


class DistributorAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    distributor_id: UUID
    distributor_name: str

    total_salespersons: int
    total_sellers: int

    total_sales: int
    total_sales_amount: Decimal

    outstanding_due: Decimal
    verified_payments: Decimal

    pending_payment_proofs: int
    pending_stock_requests: int

    total_inventory_quantity: Decimal

    top_products: list[TopProductAnalytics]
    seller_performance: list[SellerPerformanceAnalytics]

    sales_trend: list[SalesTrendItem]


class SellerAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seller_id: UUID
    seller_name: str

    total_sales: int
    total_sales_amount: Decimal

    outstanding_due: Decimal
    verified_payments: Decimal

    total_payment_proofs: int
    pending_payment_proofs: int

    total_products: int
    total_quantity: Decimal

    sales_trend: list[SalesTrendItem]



class RevenueSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_revenue: Decimal
    total_sales: int
    average_sale_value: Decimal


class RevenueTrendItem(BaseModel):
    date: date
    sales_count: int
    revenue: Decimal


class RevenueByProductItem(BaseModel):
    product_id: UUID
    product_name: str
    quantity_sold: Decimal
    revenue: Decimal


class RevenueByDistributorItem(BaseModel):
    distributor_id: UUID
    distributor_name: str
    sales_count: int
    revenue: Decimal


class RevenueBySellerItem(BaseModel):
    seller_id: UUID
    seller_name: str
    sales_count: int
    revenue: Decimal