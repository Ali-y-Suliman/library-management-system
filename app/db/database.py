import logging
from sqlalchemy import create_engine, text
from app.core.config import settings
from sqlalchemy.ext.declarative import declarative_base


logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)

Base = declarative_base()


def sql(query, **params):
    para = dict(**params)
    with engine.begin() as conn:
        result = conn.execute(text(query), para)

    return SQLHelper(result)


class SQLHelper:
    def __init__(self, exec_res):
        self.exec_res = exec_res

    def dict(self):
        res = [dict(row) for row in self.exec_res.mappings().all()]
        if not res:
            return {}
        return res[0]

    def dicts(self):
        return [dict(row) for row in self.exec_res.mappings().all()]

    def scalar(self):
        d = self.dict()
        if not d:
            return None
        return list(d.values())[0]

    def scalars(self):
        d = self.dicts()
        if not d:
            return []
        return [list(r.values())[0] for r in d]
