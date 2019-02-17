import os

from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager

from resources.user import UserRegister
from resources.item import Item, ItemList
from resources.store import Store, StoreList
from resources.user import User, UserList, UserLogin, UserLogout
from resources.token import TokenRefresh, TokenList
from models.token_blacklist import BlacklistToken

app = Flask(__name__)
app.secret_key = '28dd16028dd1602e2b7b92b2b7b92b79e7e40189df5f30e7e40189df5f30'

l_db = 'sqlite:///data.db'

# Turn off the Flask-SQLAlchemy modification tracker.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Allow the Flask app to see errors from other modules.
app.config['PROPAGATE_EXCEPTIONS'] = True

# Database URI
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', l_db)

# Enable Token Blacklist
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_CHECKS'] = ['access', 'refresh']

api = Api(app)
jwt = JWTManager(app)


@jwt.token_in_blacklist_loader
def token_in_blacklist_callback(decoded_token):
    return BlacklistToken.is_token_revoked(decoded_token)


@jwt.expired_token_loader
def expired_token_callback():
    return jsonify({
        'error_code': 'token_expired',
        'error': 'Token has expired.'
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error_code': 'token_invalid',
        'error': 'Signature verfication failed.'
    }), 401


@jwt.unauthorized_loader
def unauthorized_token_callback(error):
    return jsonify({
        'error_code': 'token_not_authorized',
        'error': 'Token is not authorized.'
    }), 401


@jwt.needs_fresh_token_loader
def needs_fresh_token_callback():
    return jsonify({
        'error_code': 'token_need_fresh',
        'error': 'Token needs to be fresh.'
    }), 401


@jwt.revoked_token_loader
def revoked_token_callback():
    return jsonify({
        'error_code': 'token_revoked',
        'error': 'Token has been revoked.'
    }), 401


api.add_resource(Item, '/item/<string:name>')
api.add_resource(ItemList, '/items')

api.add_resource(Store, '/store/<string:name>')
api.add_resource(StoreList, '/stores')

api.add_resource(UserLogin, '/auth/login')
api.add_resource(UserLogout, '/auth/logout')
api.add_resource(UserRegister, '/auth/register')
api.add_resource(TokenRefresh, '/auth/refresh')
api.add_resource(TokenList, '/auth/tokens')

api.add_resource(User, '/user/<int:user_id>')
api.add_resource(UserList, '/users')



# Create DB tables, if they do not exists.
@app.before_first_request
def create_db_tables():
    db.create_all()


if __name__ == '__main__':  # make sure, not to run this code again on import.
    from db import db
    db.init_app(app)
    app.run(port=5000)
