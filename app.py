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

# Message Strings Start
TOKEN_AUTH_TOKEN_EXPIRED = "Token has expired"
TOKEN_AUTH_TOKEN_INVALID = "Token is invalid."
TOKEN_AUTH_TOKEN_NEED_FRESH = "Token needs to be fresh."
TOKEN_AUTH_TOKEN_REVOKED = "Token has been revoked!"
# Message Strings End

app = Flask(__name__)
app.secret_key = "28dd16028dd1602e2b7b92b2b7b92b79e7e40189df5f30e7e40189df5f30"

l_db = "sqlite:///data.db"

# Turn off the Flask-SQLAlchemy modification tracker.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Allow the Flask app to see errors from other modules.
app.config["PROPAGATE_EXCEPTIONS"] = True

# Database URI
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", l_db)

# Enable Token Blacklist
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_CHECKS"] = ["access", "refresh"]

api = Api(app)
jwt = JWTManager(app)


@jwt.token_in_blacklist_loader
def token_in_blacklist_callback(decoded_token):
    return BlacklistToken.is_token_revoked(decoded_token)


@jwt.expired_token_loader
def expired_token_callback():
    return jsonify({"code": "token_expired", "message": TOKEN_AUTH_TOKEN_EXPIRED}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return (
        jsonify({"code": "token_invalid", "message": TOKEN_AUTH_TOKEN_INVALID}),
        401,
    )


@jwt.unauthorized_loader
def unauthorized_token_callback(error):
    return (
        jsonify(
            {"code": "token_invalid", "message": TOKEN_AUTH_TOKEN_INVALID}
        ),
        401,
    )


@jwt.needs_fresh_token_loader
def needs_fresh_token_callback():
    return (
        jsonify({"code": "token_need_fresh", "message": TOKEN_AUTH_TOKEN_NEED_FRESH}),
        401,
    )


@jwt.revoked_token_loader
def revoked_token_callback():
    return jsonify({"code": "token_revoked", "message": TOKEN_AUTH_TOKEN_REVOKED}), 401


api.add_resource(Item, "/item/<string:name>")
api.add_resource(ItemList, "/items")

api.add_resource(Store, "/store/<string:name>")
api.add_resource(StoreList, "/stores")

api.add_resource(UserLogin, "/auth/login")
api.add_resource(UserLogout, "/auth/logout")
api.add_resource(UserRegister, "/auth/register")
api.add_resource(TokenRefresh, "/auth/refresh")
api.add_resource(TokenList, "/auth/tokens")

api.add_resource(User, "/user/<int:user_id>")
api.add_resource(UserList, "/users")
