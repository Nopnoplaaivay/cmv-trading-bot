from typing import List, TypeVar, Generic, Dict, Union, Callable

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.modules.base.entities import Base
from backend.modules.base.query_builder import BaseQueryBuilder, TextSQL

T = TypeVar("T", bound=Base)


class BaseRepo(Generic[T]):
    entity: T
    query_builder: BaseQueryBuilder
    session_scope: Callable[..., Session]

    @classmethod
    async def data_frame_factory(cls, cur) -> pd.DataFrame:
        if cur.description is None:
            return pd.DataFrame()
        columns = [column[0] for column in cur.description]
        results = [list(row) for row in cur.fetchall()]
        return pd.DataFrame(results, columns=columns, dtype=np.dtype("O"))

    @classmethod
    async def row_factory(cls, cur) -> List[Dict]:
        if cur.description is None:
            return []
        columns = [column[0] for column in cur.description]
        results = []
        for row in cur.fetchall():
            results.append(dict(zip(columns, row)))
        return results

    @classmethod
    async def insert_many(cls, records: List[Dict], returning):
        with cls.session_scope() as session:
            insert_query = cls.query_builder.insert_many(records=records, returning=returning)
            cur = session.connection().exec_driver_sql(insert_query.sql, tuple(insert_query.params)).cursor
            if returning:
                return await cls.row_factory(cur=cur)
            else:
                return None

    @classmethod
    async def insert(cls, record: Dict, returning) -> Dict:
        results = await cls.insert_many(records=[record], returning=returning)
        if returning:
            return results[0]
        else:
            return None

    @classmethod
    async def update_many(
        cls, records: List[Dict], identity_columns: List[str], returning, text_clauses: Dict[str, TextSQL] = None
    ):
        if len(identity_columns) == 0:
            raise Exception("missing require identity columns")
        with cls.session_scope() as session:
            query_values = cls.query_builder.generate_values(records=records, text_clauses=text_clauses)
            update_columns = query_values.columns.copy()
            for col in identity_columns:
                update_columns.remove(col)
            sql_set_columns = ", ".join([f"t.[{col}] = s.[{col}]" for col in update_columns])
            sql_select_columns = ", ".join(f"[{col}]" for col in query_values.columns)
            sql_conditions = " AND ".join([f"t.[{col}] = s.[{col}]" for col in identity_columns])
            sql_returning = "OUTPUT INSERTED.*" if returning else ""
            sql = f"""
                UPDATE t
                SET {sql_set_columns}
                {sql_returning}
                FROM (
                    SELECT *
                    from (
                        {query_values.sql}
                    ) _ ({sql_select_columns})
                ) s
                inner join {cls.query_builder.full_table_name} t on {sql_conditions}
            """
            cur = session.connection().exec_driver_sql(sql, tuple(query_values.params)).cursor
            if returning:
                results = await cls.row_factory(cur=cur)
            else:
                results = None
        return results

    @classmethod
    async def update(
        cls, record: Dict, identity_columns: List[str], returning, text_clauses: Dict[str, TextSQL] = None
    ) -> T:
        results = await cls.update_many(
            records=[record], identity_columns=identity_columns, returning=returning, text_clauses=text_clauses
        )
        if returning:
            return results[0]
        else:
            return None

    @classmethod
    async def get_all(cls) -> List[Dict]:
        with cls.session_scope() as session:
            sql = (
                """
                SELECT *
                FROM %s
            """
                % cls.query_builder.full_table_name
            )
            cur = session.connection().exec_driver_sql(sql).cursor
            results = await cls.row_factory(cur=cur)
        return results

    @classmethod
    async def insert_into_temp(
        cls, records: Union[List[Dict], pd.DataFrame], temp_table: str, text_clauses: Dict[str, TextSQL] = None
    ):
        if len(records) == 0:
            return None
        records = pd.DataFrame(records, dtype=np.dtype("O")).replace({np.nan: None})
        chunk_size = 1
        query_values = cls.query_builder.generate_values(records=records.iloc[:chunk_size], text_clauses=text_clauses)
        sql_columns = ", ".join(f"[{col}]" for col in query_values.columns)
        params = records.values.tolist()
        with cls.session_scope() as session:
            session.connection().exec_driver_sql(
                f"""
                    IF OBJECT_ID('tempdb..{temp_table}') IS NULL
                    BEGIN
                        declare @temp {cls.entity.__sqlServerType__}
                        select *
                        into {temp_table}
                        from @temp
                    END
                """
            )
            sql = f"""
                INSERT INTO {temp_table} ({sql_columns})
                {query_values.sql}
            """
            for i in range(0, len(params), 10000):
                debug_tuple = tuple(params[i : i + 10000])
                session.connection().exec_driver_sql(sql, tuple(params[i : i + 10000]))
        return query_values

    @classmethod
    async def upsert_from_source_table(
        cls, source_table, identity_columns: List[str], upsert_columns: List[str], is_update=True, is_insert=True
    ):
        sql_join_conditions = " AND ".join([f"t.[{col}] = s.[{col}]" for col in identity_columns])
        # sql update
        sql_set_columns = ", ".join([f"t.[{col}] = s.[{col}]" for col in upsert_columns if col not in identity_columns])
        sql_update = f"""
            UPDATE t
            SET {sql_set_columns}
            FROM {cls.query_builder.full_table_name} t
            JOIN {source_table} s ON {sql_join_conditions}
        """
        # sql insert
        sql_select_columns = ", ".join(f"s.[{col}]" for col in upsert_columns)
        sql_insert_columns = ", ".join(f"[{col}]" for col in upsert_columns)
        sql_insert_conditions = " or ".join([f"t.[{col}] is null" for col in identity_columns])
        sql_insert_conditions = (
            f"""
            LEFT JOIN {cls.query_builder.full_table_name} t ON {sql_join_conditions}
            WHERE {sql_insert_conditions}
        """
            if identity_columns
            else ""
        )
        sql_insert = f"""
            INSERT INTO {cls.query_builder.full_table_name} ({sql_insert_columns})
            SELECT {sql_select_columns}
            FROM {source_table} s
            {sql_insert_conditions}
        """
        list_sql = [sql_update] if is_update and len(identity_columns) != 0 else []
        if is_insert:
            list_sql += [sql_insert]
        list_sql = (
            [
                "SET NOCOUNT ON",
                # f"SET IDENTITY_INSERT  {cls.query_builder.full_table_name} ON"
            ]
            + list_sql
            + [
                # f"SET IDENTITY_INSERT  {cls.query_builder.full_table_name} OFF"
            ]
        )
        sql = ";\n".join(list_sql)
        with cls.session_scope() as session:
            session.connection().exec_driver_sql(sql)
        return

    @classmethod
    async def get_by_id(cls, _id: int):
        return await cls.get_by_condition({cls.entity.id.name: _id})

    @classmethod
    async def get_by_condition(cls, conditions: Dict):
        condition_query = cls.query_builder.where(conditions)
        sql = """
            SELECT *
            FROM
            %s
            WHERE %s
        """ % (
            cls.query_builder.full_table_name,
            condition_query.sql,
        )
        with cls.session_scope() as session:
            cur = session.connection().exec_driver_sql(sql, tuple(condition_query.params)).cursor
            records = await cls.row_factory(cur=cur)
            return records

    @classmethod
    async def insert_on_conflict_do_nothing(
        cls,
        temp_table: str,
        records: Union[List[Dict], pd.DataFrame],
        identity_columns: List[str],
        text_clauses: Dict[str, TextSQL] = None,
    ):
        with cls.session_scope() as session:
            # temp_table = f"#{cls.query_builder.table}"
            query = await cls.insert_into_temp(records=records, temp_table=temp_table, text_clauses=text_clauses)
            await cls.upsert_from_source_table(
                source_table=temp_table,
                upsert_columns=query.columns,
                identity_columns=identity_columns,
                is_update=False,
            )
            session.connection().exec_driver_sql(f"DELETE FROM {temp_table}")
        return

    @classmethod
    async def upsert(
        cls,
        temp_table: str,
        records: Union[List[Dict], pd.DataFrame],
        identity_columns: List[str],
        text_clauses: Dict[str, TextSQL] = None,
    ):
        with cls.session_scope() as session:
            # temp_table = f"#{cls.query_builder.table}"
            query = await cls.insert_into_temp(records=records, temp_table=temp_table, text_clauses=text_clauses)
            await cls.upsert_from_source_table(
                source_table=temp_table, upsert_columns=query.columns, identity_columns=identity_columns
            )
            session.connection().exec_driver_sql(f"DROP TABLE {temp_table}")
        return

    @classmethod
    async def get_order_columns(cls):
        with cls.session_scope() as session:
            sql = """
                SELECT *
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                ORDER BY COLUMN_NAME ASC
            """
            cur = session.connection().exec_driver_sql(sql, (cls.query_builder.schema, cls.query_builder.table)).cursor
            order_columns = await cls.row_factory(cur)
            return [col["COLUMN_NAME"] for col in order_columns]


    @classmethod
    async def delete(cls, conditions: Dict):
        condition_query = cls.query_builder.where(conditions)
        sql = """
            DELETE FROM %s
            WHERE %s
        """ % (
            cls.query_builder.full_table_name,
            condition_query.sql,
        )
        with cls.session_scope() as session:
            session.connection().exec_driver_sql(sql, tuple(condition_query.params))