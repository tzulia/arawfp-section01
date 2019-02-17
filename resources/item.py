from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from models.item import ItemModel
from models.store import StoreModel

# Message Strings Start #
PARSER_BLANK_ERROR = "'{}' cannot be blank."
ITEM_NOT_FOUND_ERROR = "Item not found"
ITEM_ALREADY_EXISTS_ERROR = "Item already exists!"
ITEM_STORE_NOT_FOUND_ERROR = "A Store with the name '{}' was not found."
ITEM_DB_ERROR = "The server did not answer in time, please try again later."
ITEM_DELETED_SUCCESSFULLY = "Item {} deleted!"
# Message String End #


class Item(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "price", type=float, required=True, help=PARSER_BLANK_ERROR.format("price")
    )
    parser.add_argument(
        "store_name",
        type=str,
        required=True,
        help=PARSER_BLANK_ERROR.format("store_name"),
    )

    @classmethod
    @jwt_required
    def get(cls, name: str):
        item = ItemModel.find_by_name(name)

        if item:
            return item.json()

        return {"error": ITEM_NOT_FOUND_ERROR}, 404

    @classmethod
    @jwt_required
    def post(cls, name: str):
        if ItemModel.find_by_name(name):
            return {"error": ITEM_ALREADY_EXISTS_ERROR}, 400

        data = Item.parser.parse_args()
        store = StoreModel.find_by_name(data["store_name"])

        if not store:
            return (
                {"error": ITEM_STORE_NOT_FOUND_ERROR.format(data["store_name"])},
                404,
            )

        new_item = ItemModel(name, data["price"], store.id)

        try:
            new_item.save_to_db()
        except Exception:
            return {"error": ITEM_DB_ERROR}, 500

        return new_item.json(), 201

    @classmethod
    @jwt_required
    def put(cls, name: str):
        data = Item.parser.parse_args()

        item = ItemModel.find_by_name(name)
        if item:
            # Update it
            item.price = data["price"]

            store = StoreModel.find_by_name(data["store_name"])
            if store:
                item.store_id = store.id

            try:
                item.save_to_db()
            except Exception:
                return {"error": ITEM_DB_ERROR}, 500

            return item.json()
        else:
            # Create it.
            store = StoreModel.find_by_name(data["store_name"])
            if not store:
                return (
                    {"error": ITEM_STORE_NOT_FOUND_ERROR.format(data["store_name"])},
                    404,
                )

            new_item = ItemModel(name, data["price"], store.id)

            try:
                new_item.save_to_db()
            except Exception:
                return {"error": ITEM_DB_ERROR}, 500

            return new_item.json(), 201

    @classmethod
    @jwt_required
    def delete(cls, name: str):
        item = ItemModel.find_by_name(name)
        if not item:
            return {"error": ITEM_NOT_FOUND_ERROR}, 400

        item.delete_from_db()

        return {"message": ITEM_DELETED_SUCCESSFULLY.format(name)}


class ItemList(Resource):
    @classmethod
    @jwt_required
    def get(cls):
        return {"items": [item.json() for item in ItemModel.find_all()]}
