from flask_restful import Resource
from flask_jwt_extended import jwt_required

from models.store import StoreModel


class Store(Resource):

    @jwt_required
    def get(self, name):
        store = StoreModel.find_by_name(name)
        if store:
            return store.json(-1)

        return {'message': 'Store not found'}, 404

    @jwt_required
    def post(self, name):
        if StoreModel.find_by_name(name):
            return {'error': 'Store already exists!'}, 400

        new_store = StoreModel(name)
        try:
            new_store.save_to_db()
        except Exception:
            return {'message': 'Failed to create new store.'}, 500

        return new_store.json(), 201

    @jwt_required
    def delete(self, name):
        store = StoreModel.find_by_name(name)

        if store:
            store.delete_from_db()

        return {'message': 'Store deleted!'}


class StoreList(Resource):

    @jwt_required
    def get(self):
        return {
            'stores': [store.json() for store in StoreModel.find_all()]
        }
