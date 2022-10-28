import sqlalchemy
from flask_login import UserMixin

from .db_session import SqlAlchemyBase


class Device(SqlAlchemyBase, UserMixin):
    __tablename__ = 'device'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    name = sqlalchemy.Column(sqlalchemy.String, default="принтер")
    working = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    okey = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    queue = sqlalchemy.Column(sqlalchemy.PickleType, default=[])
