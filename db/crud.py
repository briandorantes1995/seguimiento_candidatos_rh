from sqlmodel import Session, SQLModel
from pydantic import BaseModel
from helpers import utc_now


def insert_db_element(db: Session, element: SQLModel) -> SQLModel:
    db.add(element)
    db.commit()
    db.refresh(element)
    return element


def update_db_element(db: Session,original_element: SQLModel,element_update: BaseModel) -> SQLModel:

    data = element_update.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(original_element, key, value)

    if hasattr(original_element, "updated_at"):
        original_element.updated_at = utc_now()

    db.add(original_element)
    db.commit()
    db.refresh(original_element)

    return original_element


def delete_db_element(db: Session, element: SQLModel):
    db.delete(element)
    db.commit()

