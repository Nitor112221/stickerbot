import datetime
import sqlalchemy
from data.db_session import SqlAlchemyBase


class Photo(SqlAlchemyBase):
    __tablename__ = 'photo'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    id_template = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('template.id'))
    name_photo = sqlalchemy.Column(sqlalchemy.String)
