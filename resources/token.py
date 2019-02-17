from flask_restful import Resource, reqparse
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    jwt_refresh_token_required,
    create_access_token,
)

from models.token_blacklist import BlacklistToken
from models.user import UserModel


class TokenList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("hide_revoked", type=bool, required=False, default=True)

    @classmethod
    @jwt_required
    def get(cls):
        user_id = get_jwt_identity()
        tokens = BlacklistToken.get_all_tokens_by_user_id(user_id)

        if tokens:
            return {"tokens": [t.json() for t in tokens]}

        return {"tokens": []}

    @classmethod
    @jwt_required
    def post(cls):
        data = cls.parser.parse_args()
        user_id = get_jwt_identity()
        tokens = BlacklistToken.get_all_tokens_by_user_id(user_id)

        if data["hide_revoked"]:
            if tokens:
                tokens_without_revoked = [
                    token for token in tokens if not token.revoked
                ]
                return {"tokens": [token.json() for token in tokens_without_revoked]}
        else:
            if tokens:
                return {"tokens": [token.json() for token in tokens]}

        return {"tokens": []}


class TokenRefresh(Resource):
    @classmethod
    @jwt_refresh_token_required
    def post(cls):
        user_id = get_jwt_identity()
        new_token = create_access_token(identity=user_id, fresh=False)

        new_blacklist_token = BlacklistToken(new_token)
        new_blacklist_token.save_to_db()

        return {"access_token": new_token}, 200
