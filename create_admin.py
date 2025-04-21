# seed_admin.py
import asyncio

from app.db.database import async_session
from app.db.crud.crud_role import get_role_by_name, create_role
from app.db.crud.crud_user import get_user_by_email, create_user


async def create_admin_user():
    async with async_session() as session:
        # 1) Define your admin user’s credentials
        admin_email = "admin@example.com"
        admin_password = "secureAdminPassword"
        first_name = "Site"
        last_name = "Administrator"

        # 2) Skip if already exists
        existing = await get_user_by_email(session, admin_email)
        if existing:
            print(f"Admin user '{admin_email}' already exists, skipping.")
            return

        # 3) Ensure the 'admin' role exists
        role = await get_role_by_name(session, "admin")
        if not role:
            print("Role 'admin' not found—creating it.")
            role = await create_role(session, "admin")

        # 4) Create the user (create_user will hash the password for you)
        user = await create_user(
            session,
            email=admin_email,
            password=admin_password,
            first_name=first_name,
            last_name=last_name,
            mobile_phone=None,
            organisation=None,
            research_id_doc=None,
            ethics_approval_doc=None,
            confidentiality_agreement_doc=None,
            role_objs=[role],
            hashed=False,  # password is plain text, let create_user hash it
        )

        print(f"Admin user '{admin_email}' created with role 'admin' (id={user.id}).")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
