import uuid

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.permissions.models import Permission
from app.roles.models import Role
from app.users.models import User


ROLES = {
    "SUPER ADMIN": "Full system administration access",
    "MASTER ADMIN": "Organization-wide administrative access",
    "DISTRIBUTOR": "Distributor-level operational access",
    "SALESPERSON": "Salesperson-level operational access",
    "FINANCE USER": "Payment, due and reporting access",
}


PERMISSIONS = {
    "distributor.create": "Create distributors",
    "distributor.view": "View distributors",
    "distributor.update": "Update distributors",

    "salesperson.create": "Create salespersons",
    "salesperson.view": "View salespersons",
    "salesperson.update": "Update salespersons",

    "seller.create": "Create sellers",
    "seller.view": "View sellers",
    "seller.update": "Update sellers",

    "product.view": "View products",
    "product.create": "Create products",
    "product.update": "Update products",

    "inventory.view": "View inventory",
    "inventory.manage": "Manage inventory",

    "stock_request.create": "Create stock requests",
    "stock_request.view": "View stock requests",
    "stock_request.approve": "Approve stock requests",
    "stock_request.reject": "Reject stock requests",

    "sale.create": "Create sales",
    "sale.view": "View sales",

    "payment_proof.create": "Create payment proofs",
    "payment_proof.view": "View payment proofs",
    "payment_proof.verify": "Verify payment proofs",
    "payment_proof.reject": "Reject payment proofs",

    "due.view": "View outstanding dues",

    "report.view": "View reports",
}


# PRD defines the permission types.
# Role assignment below is intentionally conservative and follows
# the capabilities described for each role in the PRD.
ROLE_PERMISSIONS = {
    "SUPER ADMIN": set(PERMISSIONS.keys()),

    "MASTER ADMIN": set(PERMISSIONS.keys()),

    "DISTRIBUTOR": {
        "distributor.view",
        "salesperson.create",
        "salesperson.view",
        "salesperson.update",
        "seller.create",
        "seller.view",
        "seller.update",
        "product.view",
        "inventory.view",
        "inventory.manage",
        "stock_request.view",
        "stock_request.approve",
        "stock_request.reject",
        "sale.create",
        "sale.view",
        "payment_proof.view",
        "payment_proof.verify",
        "payment_proof.reject",
        "due.view",
        "report.view",
    },

    "SALESPERSON": {
        "seller.create",
        "seller.view",
        "seller.update",
        "product.view",
        "inventory.view",
        "stock_request.create",
        "stock_request.view",
        "sale.create",
        "sale.view",
        "payment_proof.create",
        "payment_proof.view",
        "due.view",
    },

    "FINANCE USER": {
        "payment_proof.view",
        "payment_proof.verify",
        "payment_proof.reject",
        "due.view",
        "report.view",
    },
}


ADMIN_EMAIL = "admin@bacchus.com"
ADMIN_PASSWORD = "Bacchus@123"


def get_or_create_role(db, name: str, description: str) -> Role:
    role = db.scalar(
        select(Role).where(Role.name == name)
    )

    if role is None:
        role = Role(
            id=uuid.uuid4(),
            name=name,
            description=description,
            is_active=True,
        )
        db.add(role)
        db.flush()

    return role


def get_or_create_permission(
    db,
    code: str,
    description: str,
) -> Permission:
    permission = db.scalar(
        select(Permission).where(Permission.code == code)
    )

    if permission is None:
        permission = Permission(
            id=uuid.uuid4(),
            code=code,
            description=description,
            is_active=True,
        )
        db.add(permission)
        db.flush()

    return permission


def seed():
    db = SessionLocal()

    try:
        # ---------------------------------------------------------
        # 1. Permissions
        # ---------------------------------------------------------
        permission_map = {}

        for code, description in PERMISSIONS.items():
            permission_map[code] = get_or_create_permission(
                db,
                code,
                description,
            )

        # ---------------------------------------------------------
        # 2. Roles
        # ---------------------------------------------------------
        role_map = {}

        for name, description in ROLES.items():
            role_map[name] = get_or_create_role(
                db,
                name,
                description,
            )

        # ---------------------------------------------------------
        # 3. Role -> Permission mapping
        # ---------------------------------------------------------
        for role_name, permission_codes in ROLE_PERMISSIONS.items():
            role = role_map[role_name]

            existing_permission_ids = {
                permission.id
                for permission in role.permissions
            }

            for permission_code in permission_codes:
                permission = permission_map[permission_code]

                if permission.id not in existing_permission_ids:
                    role.permissions.append(permission)

        # ---------------------------------------------------------
        # 4. Initial SUPER ADMIN
        # ---------------------------------------------------------
        super_admin_role = role_map["SUPER ADMIN"]

        admin = db.scalar(
            select(User).where(User.email == ADMIN_EMAIL)
        )

        if admin is None:
            admin = User(
                id=uuid.uuid4(),
                role_id=super_admin_role.id,
                email=ADMIN_EMAIL,
                mobile=None,
                password_hash=hash_password(ADMIN_PASSWORD),
                is_active=True,
            )

            db.add(admin)

        else:
            # Make sure the existing seed account has the correct role.
            admin.role_id = super_admin_role.id
            admin.is_active = True

        db.commit()

        print()
        print("=" * 60)
        print("BACCHUS DATABASE SEED COMPLETED")
        print("=" * 60)
        print()
        print("SUPER ADMIN")
        print(f"Email    : {ADMIN_EMAIL}")
        print(f"Password : {ADMIN_PASSWORD}")
        print()
        print("Roles seeded       :", len(ROLES))
        print("Permissions seeded :", len(PERMISSIONS))
        print()
        print("=" * 60)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()