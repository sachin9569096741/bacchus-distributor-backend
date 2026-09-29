from fastapi import APIRouter, Depends

from app.permissions.dependencies import require_permission
from app.users.models import User

router = APIRouter(prefix="/permissions", tags=["Permissions"])


