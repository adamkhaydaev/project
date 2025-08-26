import secrets
import string
from datetime import datetime, timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

# Создаем простую базу данных прямо здесь
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

# SQLite база данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Модель для хранения кликов
class URLClick(Base):
    __tablename__ = "url_clicks"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"))
    clicked_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)


# Модели
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    alias = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    clicks_count = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Связь с кликами
    clicks = relationship("URLClick", backref="url", cascade="all, delete-orphan")


# Pydantic модель для ответа статистики
class DetailedStatsResponse(BaseModel):
    link: str
    orig_link: str
    last_hour_clicks: int
    last_day_clicks: int
    total_clicks: int
    created_at: datetime
    expires_at: datetime
    is_active: bool


# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Alias Service",
    description="Сервис для создания коротких ссылок с расширенной статистикой",
    version="1.0.0",
)

security = HTTPBasic()


# Функция для получения базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Функция для генерации случайного alias
def generate_alias(length=8):
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


# Функция для аутентификации
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if user and user.hashed_password == password:
        return user
    return None


@app.get("/")
def read_root():
    """Корневой эндпоинт с информацией о сервисе"""
    return {
        "message": "URL Alias Service",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "create_url": "/urls/ (POST)",
            "list_urls": "/urls/ (GET)",
            "stats": "/stats/detailed/ (GET)",
            "redirect": "/{alias} (GET)",
        },
    }


@app.post("/register/", status_code=status.HTTP_201_CREATED)
def register_user(username: str, password: str, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    user = User(username=username, hashed_password=password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User created successfully",
        "username": user.username,
        "created_at": user.created_at,
    }


@app.post("/urls/", status_code=status.HTTP_201_CREATED)
def create_url(
    original_url: str,
    expiration_days: int = 30,
    db: Session = Depends(get_db),
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Создание короткой ссылки"""
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    alias = generate_alias()
    while db.query(URL).filter(URL.alias == alias).first():
        alias = generate_alias()

    expires_at = datetime.utcnow() + timedelta(days=expiration_days)

    db_url = URL(
        original_url=original_url, alias=alias, expires_at=expires_at, owner_id=user.id
    )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return {
        "id": db_url.id,
        "original_url": db_url.original_url,
        "alias": db_url.alias,
        "short_url": f"http://localhost:8000/{db_url.alias}",
        "expires_at": db_url.expires_at,
        "created_at": db_url.created_at,
    }


@app.get("/urls/")
def list_urls(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Получение списка всех ссылок"""
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    query = db.query(URL).filter(URL.owner_id == user.id)
    if active_only:
        query = query.filter(URL.is_active == True)

    urls = query.offset(skip).limit(limit).all()
    return urls


@app.post("/urls/{url_id}/deactivate")
def deactivate_url(
    url_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Деактивация ссылки"""
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    db_url = db.query(URL).filter(URL.id == url_id, URL.owner_id == user.id).first()
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    db_url.is_active = False
    db.commit()
    db.refresh(db_url)

    return db_url


@app.get("/stats/detailed/", response_model=List[DetailedStatsResponse])
def get_detailed_stats(
    db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)
):
    """Получение расширенной статистики по переходам"""
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    urls = db.query(URL).filter(URL.owner_id == user.id).all()

    detailed_stats = []

    for url in urls:
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        last_hour_clicks = (
            db.query(URLClick)
            .filter(URLClick.url_id == url.id, URLClick.clicked_at >= one_hour_ago)
            .count()
        )

        last_day_clicks = (
            db.query(URLClick)
            .filter(URLClick.url_id == url.id, URLClick.clicked_at >= one_day_ago)
            .count()
        )

        short_link = f"http://localhost:8000/{url.alias}"

        detailed_stats.append(
            {
                "link": short_link,
                "orig_link": url.original_url,
                "last_hour_clicks": last_hour_clicks,
                "last_day_clicks": last_day_clicks,
                "total_clicks": url.clicks_count,
                "created_at": url.created_at,
                "expires_at": url.expires_at,
                "is_active": url.is_active,
            }
        )

    detailed_stats.sort(key=lambda x: x["total_clicks"], reverse=True)

    return detailed_stats


@app.get("/{alias}")
def redirect_url(alias: str, db: Session = Depends(get_db), request: Request = None):
    """Перенаправление по короткой ссылке"""
    db_url = db.query(URL).filter(URL.alias == alias).first()
    if not db_url or not db_url.is_active or db_url.expires_at < datetime.utcnow():
        raise HTTPException(status_code=404, detail="URL not found or expired")

    db_url.clicks_count += 1

    click = URLClick(
        url_id=db_url.id,
        clicked_at=datetime.utcnow(),
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    db.add(click)
    db.commit()
    db.refresh(db_url)

    return {"redirect_url": db_url.original_url}


@app.get("/health/")
def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}
