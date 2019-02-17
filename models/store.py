from typing import Dict, List, Union

from db import db

from models.item import ItemJSON

StoreJSON = Dict[str, Union[int, str, List[ItemJSON]]]


class StoreModel(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

    items = db.relationship("ItemModel", lazy="dynamic")

    def __init__(self, name: str):
        self.name = name

    def json(self, limit: int = 10) -> StoreJSON:
        """
            This function returns the StoreModel object in json format.
            Normally it only fetches the first 10 items in the store, though
            that can be overridden by passing in -1 in the first argument.

            ::params limit:: The amount of items to fetch from the DB.
        """
        return {
            "id": self.id,
            "name": self.name,
            "items": [item.json() for item in self.items.limit(limit).all()],
        }

    @classmethod
    def find_by_name(cls, name) -> "StoreModel":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_all(cls) -> List["StoreModel"]:
        return cls.query.all()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
