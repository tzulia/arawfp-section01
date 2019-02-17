from flask_restful import Resource
from flask_jwt_extended import jwt_required

from models.store import StoreModel

# Message String Start #
STORE_NOT_FOUND_ERROR = "Store not found"
STORE_ALREADY_EXISTS_ERROR = "Store already exists!"
STORE_DELETED_SUCCESSFULLY = "Store deleted!"
STORE_DB_ERROR = "The server did not answer in time, please try again later."
# Message Strings End #


class Store(Resource):
    @jwt_required
    def get(self, name: str):
        store = StoreModel.find_by_name(name)
        if store:
            return store.json(-1)

        return {"message": STORE_NOT_FOUND_ERROR}, 404

    @jwt_required
    def post(self, name: str):
        if StoreModel.find_by_name(name):
            return {"error": STORE_ALREADY_EXISTS_ERROR}, 400

        new_store = StoreModel(name)
        try:
            new_store.save_to_db()
        except Exception:
            return {"message": STORE_DB_ERROR}, 500

        return new_store.json(), 201

    @jwt_required
    def delete(self, name: str):
        store = StoreModel.find_by_name(name)

        if store:
            store.delete_from_db()

        return {"message": "Store deleted!"}


class StoreList(Resource):
    @jwt_required
    def get(self):
        return {"stores": [store.json() for store in StoreModel.find_all()]}
