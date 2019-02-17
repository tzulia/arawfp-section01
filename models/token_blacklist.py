from typing import Dict, List, Union

from datetime import datetime

from flask_jwt_extended import decode_token

from db import db


TokenJSON = Dict[str, Union[int, str, bool, datetime]]


def _epoch_utc_to_datetime(epoch_utc: str):
    return datetime.fromtimestamp(epoch_utc)


def _format_datetime(dt: datetime):
    return "{:02d}/{:02d}/{} {:02d}:{:02d}:{:02d}".format(
        dt.day, dt.month, dt.year, dt.hour, dt.minute, dt.second
    )


class BlacklistToken(db.Model):
    __tablename__ = "tokens"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)
    token_type = db.Column(db.String(10), nullable=False)
    user_identity = db.Column(db.Integer, db.ForeignKey("users.id"))
    revoked = db.Column(db.Boolean, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    user = db.relationship("UserModel")

    def __init__(self, encoded_token: str):
        decoded_token = decode_token(encoded_token)
        self.jti = decoded_token["jti"]
        self.token_type = decoded_token["type"]
        self.user_identity = int(decoded_token["identity"])
        self.revoked = False
        self.expires = _epoch_utc_to_datetime(decoded_token["exp"])

    def json(self) -> TokenJSON:
        return {
            "id": self.id,
            "jti": self.jti,
            "token_type": self.token_type,
            "user_identify": self.user_identity,
            "revoked": self.revoked,
            "expires": _format_datetime(self.expires),
            "owned_by": self.user.username,
        }

    @classmethod
    def get_all_tokens_by_user_id(cls, user_id: int) -> List["BlacklistToken"]:
        return cls.query.filter_by(user_identity=user_id).all()

    @classmethod
    def is_token_revoked(cls, decoded_token: str) -> bool:
        db_token = cls.query.filter_by(jti=decoded_token["jti"]).first()

        if not db_token:
            return True

        return db_token.revoked

    @classmethod
    def revoke_all_old_refresh_tokens(cls, user_id: int) -> None:
        # get the user.
        tokens = cls.query.filter_by(
            token_type="refresh", user_identity=user_id, revoked=False
        ).all()

        for token in tokens:
            token.revoke()

    @classmethod
    def get_all(cls, filter_result: int = 10) -> List[TokenJSON]:
        return [t.json() for t in cls.query.limit(filter_result).all()]

    def revoke(self) -> bool:
        self.revoked = True
        self.save_to_db()
        return True

    def unrevoke(self) -> bool:
        self.revoked = False
        self.save_to_db()
        return True

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
