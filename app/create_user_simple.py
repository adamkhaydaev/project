from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite база данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Создаем таблицы
Base.metadata.create_all(bind=engine)


def create_default_user():
    db = SessionLocal()

    # Проверяем, существует ли пользователь
    existing_user = db.query(User).filter(User.username == "admin").first()
    if existing_user:
        print(f"Пользователь {existing_user.username} уже существует")
        return

    # Создаем тестового пользователя
    user = User(
        username="admin", hashed_password="password"
    )  # В реальном приложении используйте хеширование!

    db.add(user)
    db.commit()
    print(f"Создан пользователь: {user.username}")
    print("Логин: admin")
    print("Пароль: password")


if __name__ == "__main__":
    create_default_user()
