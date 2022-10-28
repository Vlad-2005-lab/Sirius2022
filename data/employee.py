import sqlalchemy
from flask_login import UserMixin

from .db_session import SqlAlchemyBase


class Employee(SqlAlchemyBase, UserMixin):
    __tablename__ = 'employee'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    tg_id = sqlalchemy.Column(sqlalchemy.Integer)
    name = sqlalchemy.Column(sqlalchemy.String)
    uid = sqlalchemy.Column(sqlalchemy.String, unique=True)
    creating_task = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    valid_from = sqlalchemy.Column(sqlalchemy.String, nullable=True, default=None)
    valid_to = sqlalchemy.Column(sqlalchemy.String, nullable=True, default=None)
