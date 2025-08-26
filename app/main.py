import secrets
import string
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app import models
from app.database import engine, get_db
from app.routers import items, users

models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="URL Alias Service",
    description="Сервис для создания коротких ссылок",
    version="1.0.0",
)

security = HTTPBasic()

# Подключаем роутеры
app.include_router(users.router)
app.include_router(items.router)


# Функция для генерации случайного short_code
def generate_short_code(length=8):
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


# Функция для аутентификации (СИНХРОННАЯ)
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if user and user.hashed_password == password:
        return user
    return None


@app.on_event("startup")
def startup():
    # Создаем таблицы при запуске (СИНХРОННО)
    models.Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {
        "message": "URL Shortener API",
        "endpoints": {
            "docs": "/docs",
            "health": "/health/",
            "db_test": "/db-test",
            "create_url": "POST /urls/",
            "list_urls": "GET /urls/",
        },
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

    # Генерируем уникальный short_code
    short_code = generate_short_code()
    while db.query(models.URL).filter(models.URL.short_code == short_code).first():
        short_code = generate_short_code()

    expires_at = datetime.utcnow() + timedelta(days=expiration_days)

    # Создаем URL
    db_url = models.URL(
        original_url=original_url,
        short_code=short_code,
        expires_at=expires_at,
        owner_id=user.id,
    )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return {
        "id": db_url.id,
        "original_url": db_url.original_url,
        "short_code": db_url.short_code,
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

    query = db.query(models.URL).filter(models.URL.owner_id == user.id)
    if active_only:
        query = query.filter(models.URL.is_active == True)

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

    db_url = (
        db.query(models.URL)
        .filter(models.URL.id == url_id, models.URL.owner_id == user.id)
        .first()
    )

    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    db_url.is_active = False
    db.commit()
    db.refresh(db_url)

    return db_url


@app.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    """Перенаправление по короткой ссылке"""
    # Игнорируем запросы favicon.ico
    if short_code == "favicon.ico":
        raise HTTPException(status_code=404, detail="Not found")

    db_url = db.query(models.URL).filter(models.URL.short_code == short_code).first()

    if not db_url or not db_url.is_active or db_url.expires_at < datetime.utcnow():
        raise HTTPException(status_code=404, detail="URL not found or expired")

    # Увеличиваем счетчик кликов
    db_url.clicks_count += 1
    db.commit()
    db.refresh(db_url)

    return {"redirect_url": db_url.original_url}


@app.get("/health/")
def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


# Используем функцию get_db!
@app.get("/db-test")
def test_db(db: Session = Depends(get_db)):
    try:
        users_count = db.query(models.User).count()
        return {
            "users_count": users_count,
            "message": "Database connected successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Database error"}
