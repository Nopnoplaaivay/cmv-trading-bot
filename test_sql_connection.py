from backend.db.sessions import backend_session_scope
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv(".env")
print(os.getenv("LOCAL_BACKEND_DNS"))

def test_upsert():
    data = pd.read_csv("universe_top20.csv")
    params = data.values.tolist()

    with backend_session_scope() as session:
        session.connection().exec_driver_sql(
            f"""
                IF OBJECT_ID('tempdb..#universeTop20') IS NULL
                BEGIN
                    declare @temp [BotPortfolio].[universeTop20]
                    select *
                    into #universeTop20
                    from @temp
                END
            """
        )

        sql = """
            INSERT INTO #universeTop20 ([year], [month], [symbol], [sectorL2], [cap], [averageLiquidity21], [averageLiquidity63], [averageLiquidity252], [grossProfitQoQ], [roe], [eps], [pe], [pb])
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for i in range(0, len(params), 10000):
            debug_tuple = tuple(params[i: i + 10000])
            session.connection().exec_driver_sql(sql, debug_tuple)


if __name__ == "__main__":
    # main()
    test_upsert()