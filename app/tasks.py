from typing import List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db
from .auth import get_current_user  # 認証処理をインポート

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(get_current_user)],  # 認証を適用
)


@router.post("/", response_model=schemas.Item)
def create_item_for_user(
    item: schemas.ItemCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    db_item = models.Item(**item.dict(), owner_id=current_user.id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = db.query(models.Item).filter(models.Item.owner_id == current_user.id).offset(skip).limit(limit).all()
    return items


@router.get("/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Item).filter(models.Item.id == item_id, models.Item.owner_id == current_user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=schemas.Item)
def update_item(
    item_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    db_item = db.query(models.Item).filter(models.Item.id == item_id, models.Item.owner_id == current_user.id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    for key, value in item.dict().items():
        setattr(db_item, key, value)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Item).filter(models.Item.id == item_id, models.Item.owner_id == current_user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}