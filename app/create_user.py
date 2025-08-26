import asyncio

from .database import AsyncSessionLocal, Base, engine
from .models import User


async def create_default_user():
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Проверяем, существует ли пользователь
        from sqlalchemy import select

        result = await db.execute(select(User).filter(User.username == "admin"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Пользователь {existing_user.username} уже существует")
            return

        # Создаем тестового пользователя
        user = User(username="admin", hashed_password="password")

        db.add(user)
        await db.commit()
        print(f"Создан пользователь: {user.username}")
        print("Логин: admin")
        print("Пароль: password")


if __name__ == "__main__":
    asyncio.run(create_default_user())
