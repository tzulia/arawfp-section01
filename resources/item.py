from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from models.item import ItemModel
from models.store import StoreModel


class Item(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('price', type=float, required=True, help="This field cannot be left blank!")
    parser.add_argument('store_name', type=str, required=True, help="Every item needs a store_name")

    @jwt_required
    def get(self, name):
        item = ItemModel.find_by_name(name)

        if item:
            return item.json()

        return {'error': 'Item not found'}, 404

    @jwt_required
    def post(self, name):
        if ItemModel.find_by_name(name):
            return {'error': 'Item already exists!'}, 400

        data = Item.parser.parse_args()
        store = StoreModel.find_by_name(data['store_name'])

        if not store:
            return {'error': "A Store with the name '{}' was not found.".format(data['store_name'])}, 404

        new_item = ItemModel(name, data['price'], store.id)

        try:
            new_item.save_to_db()
        except Exception:
            return {'error': 'Cannot create new item.'}, 500

        return new_item.json(), 201

    @jwt_required
    def put(self, name):
        data = Item.parser.parse_args()

        item = ItemModel.find_by_name(name)
        if item:
            # Update it
            item.price = data['price']

            store = StoreModel.find_by_name(data['store_name'])
            if store:
                item.store_id = store.id

            try:
                item.save_to_db()
            except Exception:
                return {'error': 'Cannot save item to DB, please try again later.'}, 500

            return item.json()
        else:
            # Create it.
            store = StoreModel.find_by_name(data['store_name'])
            if not store:
                return { 'error': "A store with the name '{}' was not found".format(data['store_name']) }, 404

            new_item = ItemModel(name, data['price'], store.id)

            try:
                new_item.save_to_db()
            except Exception:
                return {'error': 'Cannot save item to DB, please try again later.'}, 500
 
            return new_item.json(), 201

    @jwt_required
    def delete(self, name):
        item = ItemModel.find_by_name(name)
        if not item:
            return {'error': 'Item does not exist'}, 400

        item.delete_from_db()

        return {'message': 'Item {} deleted!'.format(name)}


class ItemList(Resource):
    @jwt_required
    def get(self):
        return {'items': list(map(lambda item: item.json(), ItemModel.find_all()))}
