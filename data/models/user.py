import datetime
import sqlalchemy
from data.db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    id_telegramm = sqlalchemy.Column(sqlalchemy.Integer, unique=True, nullable=False)
    is_add_photo = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    selected_template = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('template.id'), default=1)
    role = sqlalchemy.Column(sqlalchemy.String)
