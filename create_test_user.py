# seed_user.py
import asyncio
from app.db.database import async_session
from app.db.models import User
from app.core.security import get_password_hash


async def create_test_user():
    async with async_session() as session:
        test_email = "test@example.com"
        test_password = "testpassword"
        hashed_password = get_password_hash(test_password)
        user = User(
            email=test_email,
            hashed_password=hashed_password,
            first_name="Test",
            last_name="User",
        )
        session.add(user)
        await session.commit()
        print(f"User '{test_email}' created.")


asyncio.run(create_test_user())
