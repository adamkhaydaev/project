from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/")
def get_items(db: Session = Depends(get_db)):
    items = db.query(models.Item).all()
    return items
