from flask_restful import Resource, reqparse
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
)
from flask_jwt_extended import jwt_required
from werkzeug.security import safe_str_cmp

from models.user import UserModel
from models.token_blacklist import BlacklistToken

# Message Strings Start #
USER_NOT_FOUND_ERROR = "User not found"
PARSER_BLANK_ERROR = "'{}' cannot be blank."
USER_DELETED_SUCCESSFULLY = "User successfully deleted!"
USER_ALREADY_EXISTS_ERROR = "User {} already exists!"
USER_CREATED_SUCCESSFULLY = "User created successfully."
USER_LOGIN_SUCCESSFULLY = "User logged in successfully."
USER_LOGOUT_SUCCESSFULLY = "User logged out successfully."
TOKEN_AUTH_INVALID_CREDENTIALS = "Invalid credentials"
# Message Strings End #

_user_parser = reqparse.RequestParser()
_user_parser.add_argument(
    "username", type=str, required=True, help=PARSER_BLANK_ERROR.format("username")
)
_user_parser.add_argument(
    "password", type=str, required=True, help=PARSER_BLANK_ERROR.format("password")
)


class User(Resource):
    @classmethod
    @jwt_required
    @UserModel.require_admin
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)

        if not user:
            return {"error": USER_NOT_FOUND_ERROR}, 404
        return user.json()

    @classmethod
    @jwt_required
    @UserModel.require_admin
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)

        if not user:
            return {"error": USER_NOT_FOUND_ERROR}, 404

        user.delete_from_db()
        return {"message": USER_DELETED_SUCCESSFULLY}


class UserList(Resource):
    @classmethod
    @jwt_required
    @UserModel.require_admin
    def get(cls):
        return {"users": [user.json() for user in UserModel.get_all()]}


class UserRegister(Resource):
    @classmethod
    def post(cls):
        data = _user_parser.parse_args()

        if UserModel.find_by_username(data["username"]):
            return {"error": USER_ALREADY_EXISTS_ERROR.format(data["username"])}, 400

        new_user = UserModel(**data)
        new_user.save_to_db()

        return {"message": USER_CREATED_SUCCESSFULLY}, 201


class UserLogin(Resource):
    @classmethod
    def post(cls):
        # get data from parser
        data = _user_parser.parse_args()

        # find user in database
        user = UserModel.find_by_username(data["username"])

        # check password
        if user and safe_str_cmp(user.password, data["password"]):
            # Black list all old refresh tokens before making new ones.
            BlacklistToken.revoke_all_old_refresh_tokens(user.id)

            # create access token
            access_token = create_access_token(identity=user.id, fresh=True)
            # create refresh token
            refresh_token = create_refresh_token(identity=user.id)

            # Lets store the tokens in the DB, as non-expired.
            new_access_token = BlacklistToken(access_token)
            new_refresh_token = BlacklistToken(refresh_token)

            new_access_token.save_to_db()
            new_refresh_token.save_to_db()

            return (
                {
                    "code": "login_success",
                    "message": USER_LOGIN_SUCCESSFULLY,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
                200,
            )

        return {"error": TOKEN_AUTH_INVALID_CREDENTIALS}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required
    def post(cls):
        user_id = get_jwt_identity()
        tokens = BlacklistToken.get_all_tokens_by_user_id(user_id)

        # Revoke all tokens that this user has.
        for token in tokens:
            token.revoke()

        return ({"code": "logout_success", "message": USER_LOGOUT_SUCCESSFULLY}, 200)
