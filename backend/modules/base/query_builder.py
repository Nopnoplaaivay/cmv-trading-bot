from typing import Union, List, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from backend.modules.base.entities import Base


class TextSQL:
    def __init__(self, text: str):
        self.text = text


class QueryProduct:
    def __init__(self, sql, params, columns):
        self.sql: str = sql
        self.params: Union[Tuple, List] = params
        self.columns: List[str] = columns


class BaseQueryBuilder:
    def __init__(self, entity: Base):
        self.entity = entity
        self.schema = self.entity.__table__.schema
        self.table = self.entity.__tablename__
        self.full_table_name = f"[{self.schema}].[{self.table}]"

    @classmethod
    def generate_values(cls, records: Union[List[Dict], pd.DataFrame], text_clauses: Optional[Dict[str, TextSQL]]):
        if len(records) == 0:
            return None
        data = pd.DataFrame(records, dtype=np.dtype("O")).replace({np.nan: None})
        row = data.shape[0]
        col = data.shape[1]
        params = data.values.flatten().tolist()
        columns = list(data.columns)
        sql_value = ["?"] * col
        if text_clauses is not None:
            text_columns = list(text_clauses.keys())
            text_values = [text_clauses[i].text for i in text_columns]
            columns += text_columns
            sql_value += text_values
        sql_value = ", ".join(sql_value)
        sql_value = "(%s)" % sql_value
        sql_values = ", ".join([sql_value] * row)
        sql_values = "VALUES %s" % sql_values
        return QueryProduct(sql=sql_values, params=params, columns=columns)

    def insert_many(self, records: List[Dict], returning, text_clauses: Dict[str, TextSQL] = None):
        query_values = self.generate_values(records=records, text_clauses=text_clauses)
        sql_columns = ", ".join(f"[{col}]" for col in query_values.columns)
        sql_output = "OUTPUT Inserted.*" if returning else ""
        sql = """
            INSERT INTO %s (%s)
            %s
            %s
        """ % (self.full_table_name, sql_columns, sql_output, query_values.sql,)
        return QueryProduct(sql=sql, params=query_values.params, columns=query_values.columns)

    @classmethod
    def where(cls, conditions: Dict, alias=None):
        sql = []
        params = []
        if alias is not None and alias != "":
            alias = "%s." % alias
        else:
            alias = ""
        for field in conditions:
            value = conditions[field]
            if value is None:
                sql.append("%s[%s] IS NULL" % (alias, field))
            elif isinstance(value, (list, tuple)):
                in_value_query = ", ".join(["?" for _ in value])
                sql.append("%s[%s] in (%s)" % (alias, field, in_value_query))
                params += value
            elif isinstance(value, TextSQL):
                sql.append("%s[%s] = %s" % (alias, field, value.text))
            else:
                sql.append("%s[%s] = ?" % (alias, field))
                params.append(value)
        if len(sql) == 0:
            return QueryProduct(sql="", params=[], columns=None)
        sql = " AND ".join(sql)
        return QueryProduct(sql=sql, params=params, columns=None)
