from flask_restful import Resource, reqparse
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jwt_identity
)
from flask_jwt_extended import jwt_required
from werkzeug.security import safe_str_cmp

from models.user import UserModel
from models.token_blacklist import BlacklistToken


_user_parser = reqparse.RequestParser()
_user_parser.add_argument(
    'username',
    type=str,
    required=True,
    help="Please enter a username."
)
_user_parser.add_argument(
    'password',
    type=str,
    required=True,
    help="Please enter a password."
)


class User(Resource):
    @classmethod
    @jwt_required
    @UserModel.require_admin
    def get(cls, user_id):
        user = UserModel.find_by_id(user_id)

        if not user:
            return {
                'error': 'User not found.'
            }, 404
        return user.json()

    @classmethod
    @jwt_required
    def delete(cls, user_id):
        user = UserModel.find_by_id(user_id)

        if not user:
            return {
                'error': 'User not found.'
            }, 404

        user.delete_from_db()
        return {
            'message': 'User deleted.'
        }


class UserList(Resource):
    @classmethod
    @jwt_required
    def get(cls):
        return {
            'users': list(map(lambda user: user.json(), UserModel.get_all()))
        }


class UserRegister(Resource):
    def post(self):
        data = _user_parser.parse_args()

        if UserModel.find_by_username(data['username']):
            return {
                'error': 'User {} already exists!'.format(data['username'])
            }, 400

        if data['username'] == 'tzulia':
            data['is_admin'] = True
        else:
            data['is_admin'] = False

        new_user = UserModel(**data)
        new_user.save_to_db()

        return {'message': 'User created successfully.'}, 201


class UserLogin(Resource):
    @classmethod
    def post(cls):
        # get data from parser
        data = _user_parser.parse_args()

        # find user in database
        user = UserModel.find_by_username(data['username'])

        # check password
        if user and safe_str_cmp(user.password, data['password']):
            # create access token
            access_token = create_access_token(identity=user.id, fresh=True)
            # create refresh token
            refresh_token = create_refresh_token(identity=user.id)

            # Lets store the tokens in the DB, as non-expired.
            new_access_token = BlacklistToken(access_token)
            new_refresh_token = BlacklistToken(refresh_token)

            new_access_token.save_to_db()
            new_refresh_token.save_to_db()

            return {
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 200

        return {
            'error': 'Invalid credentials'
        }, 401


class UserLogout(Resource):
    @jwt_required
    def post(self):
        user_id = get_jwt_identity()
        tokens = BlacklistToken.get_all_tokens_by_user_id(user_id)

        # Revoke all tokens that this user has.
        for token in tokens:
            token.revoke()

        return {
            'code': 'logout_success',
            'message': 'User logged out successfully'
        }, 200
