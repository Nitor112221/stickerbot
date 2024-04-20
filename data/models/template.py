import datetime
import sqlalchemy
from data.db_session import SqlAlchemyBase


class Template(SqlAlchemyBase):
    __tablename__ = 'template'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    id_creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, unique=True)
    is_public = sqlalchemy.Column(sqlalchemy.Boolean, default=False)