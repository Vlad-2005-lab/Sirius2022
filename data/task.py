import sqlalchemy
from flask_login import UserMixin

from .db_session import SqlAlchemyBase


class Task(SqlAlchemyBase, UserMixin):
    __tablename__ = 'task'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    id_employee = sqlalchemy.Column(sqlalchemy.Integer)
    id_device = sqlalchemy.Column(sqlalchemy.Integer)
    datetime = sqlalchemy.Column(sqlalchemy.String)
    duration = sqlalchemy.Column(sqlalchemy.String, default="")
