from fastapi import FastAPI
import app.models
from app.permissions.router import router as permissions_router
import app.core.cloudinary
from app.auth.router import router as auth_router
from app.users.router import router as master_admin_router
from app.distributors.router import router as distributors_router
from app.geography.router import router as geography_router
from app.salespersons.router import router as salesperson_router
from app.sellers.router import router as seller_router
from app.products.router import router as products_router
from app.inventory.router import router as inventory_router
from app.stock_requests.router import router as stock_request_router
from app.sales.router import router as sales_router
from app.dues.router import router as dues_router
from app.payment_proofs.router import router as payment_proofs_router
from app.analytics.router import router as analytics_router
from app.report_submissions.router import router as report_submissions_router
from app.notifications.router import router as notifications_router
from app.audit.router import router as audit_router

app = FastAPI(
    title="Bacchus Distributor Management Platform",
)


app.include_router(auth_router)
app.include_router(permissions_router)
app.include_router(master_admin_router)
app.include_router(distributors_router)
app.include_router(geography_router)
app.include_router(salesperson_router)
app.include_router(seller_router)
app.include_router(products_router)
app.include_router(inventory_router)
app.include_router(stock_request_router)
app.include_router(sales_router)
app.include_router(dues_router)
app.include_router(payment_proofs_router)
app.include_router(analytics_router)

app.include_router(report_submissions_router)
app.include_router(notifications_router)
app.include_router(audit_router)