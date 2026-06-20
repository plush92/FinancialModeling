from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    model: type[ModelType]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, object_id: int):
        return self.db.get(self.model, object_id)

    def list(self, skip: int = 0, limit: int = 100):
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: CreateSchemaType):
        db_obj = self.model(**obj_in.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: UpdateSchemaType):
        update_data = obj_in.model_dump(exclude_unset=True)
        for field_name, value in update_data.items():
            setattr(db_obj, field_name, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: ModelType):
        self.db.delete(db_obj)
        self.db.commit()
        return None
