from backend.db.sessions import backend_session_scope
import os
import pandas as pd
from dotenv import load_dotenv


def test():
    with backend_session_scope() as session:

        sql = """
            SELECT [id]
                ,[date]
                ,[symbol]
                ,[initialWeight]
                ,[neutralizedWeight]
            FROM [CMVTradingBot].[BotPortfolio].[optimizedWeights]
            ORDER BY [date] ASC
        """

        records = session.connection().exec_driver_sql(sql)

        # Organize data by month
        monthly_data = {}
        for record in records:
            date_str = record[1]
            symbol = record[2]
            initial_weight = record[3]
            neutralized_weight = record[4]

            # Convert string date to datetime object
            date = pd.to_datetime(date_str)

            # Extract year-month for grouping
            year_month = f"{date.year}-{date.month:02d}"

            if year_month not in monthly_data:
                monthly_data[year_month] = []

            monthly_data[year_month].append(
                {
                    "date": date,  # Use converted datetime object
                    "symbol": symbol,
                    "initialWeight": initial_weight,
                    "neutralizedWeight": neutralized_weight,
                }
            )

        # Create DataFrame for each month and store in dictionary
        excel_data = {}
        for year_month in sorted(monthly_data.keys()):
            # Convert to DataFrame
            df_month = pd.DataFrame(monthly_data[year_month])

            # Get all unique symbols for this month
            all_symbols = sorted(df_month["symbol"].unique())

            # Create multi-level columns: (symbol, weight_type)
            columns = []
            for symbol in all_symbols:
                columns.extend(
                    [(symbol, "initialWeight"), (symbol, "neutralizedWeight")]
                )

            # Create DataFrame with date as index and multi-level columns
            dates = sorted(df_month["date"].unique())
            result_df = pd.DataFrame(
                index=dates, columns=pd.MultiIndex.from_tuples(columns)
            )

            # Fill the DataFrame
            for _, row in df_month.iterrows():
                date = row["date"]
                symbol = row["symbol"]
                result_df.loc[date, (symbol, "initialWeight")] = row["initialWeight"]
                result_df.loc[date, (symbol, "neutralizedWeight")] = row[
                    "neutralizedWeight"
                ]

            # Round to 3 decimal places
            result_df = result_df.round(3)

            # Store in dictionary for Excel export
            excel_data[year_month] = result_df

            print(f"Added {year_month} to Excel data")

        # Export all months to single Excel file with multiple sheets
        excel_filename = "tmp/portfolio_weights_all_months_2.xlsx"
        with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:
            for sheet_name, df in excel_data.items():
                df.to_excel(writer, sheet_name=sheet_name)

        print(
            f"\n✅ Successfully exported to {excel_filename} with {len(excel_data)} sheets"
        )


if __name__ == "__main__":
    # main()
    test()
