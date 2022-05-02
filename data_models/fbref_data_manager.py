from typing import List
import pandas as pd
from footmav.odm.fbref_data import FbRefData
from sqlalchemy import create_engine
from pypika import Table, MySQLQuery
import logging
from footmav import fb


class ConnectionManager:
    _connection = None

    @staticmethod
    def create_engine(user, password, host, port, db):
        return create_engine("mysql://{0}:{1}@{2}:{3}/{4}?charset=utf8".format(user, password, host, port, db))

    def __init__(self):
        if not self._connection:
            self._connection = self.create_engine("local", "Local1234!", "localhost", 3306, "football_data")

    @property
    def engine(self):
        return self._connection

    @engine.setter
    def engine(self, engine):
        raise Exception("Cannot set engine")


def get_fbref_data(start_date: str, end_date: str, columns: List[str] = None, **kwargs):
    log = logging.getLogger(__name__)
    fbref_data = Table("fbref2")
    if columns:
        query_columns = list(set(columns + [fb.PLAYER_ID.N, fb.DATE.N]))
    else:
        query_columns = [fbref_data.star]

    query = MySQLQuery.from_(fbref_data).select(*query_columns).where(fbref_data.date.between(start_date, end_date))

    for k, v in kwargs.items():
        if isinstance(v, list):
            query = query.where(getattr(fbref_data, k).isin(v))
        else:
            query = query.where(getattr(fbref_data, k) == v)
    log.info(f'Running query: "{query}"')
    df = pd.read_sql(query.get_sql(), ConnectionManager().engine)
    log.info("Query returned {0} rows".format(len(df)))
    return FbRefData(df)
