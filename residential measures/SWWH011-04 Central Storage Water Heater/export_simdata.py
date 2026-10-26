import sqlite3
import pandas as pd
from pathlib import Path

# Editable file locations
db_file = Path("simdata.sqlite")
excel_file = Path("simdata_export.xlsx")

# Tables to export
tables_to_export = [
    "sim_data",
    "sim_metadata",
    "sim_deerpeak",
]

if not db_file.exists():
    raise FileNotFoundError(f"Database not found: {db_file.resolve()}")

with sqlite3.connect(db_file) as conn:

    # Check which tables exist before attempting the export
    existing_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()
    }

    missing_tables = [
        table for table in tables_to_export
        if table not in existing_tables
    ]

    if missing_tables:
        raise ValueError(
            "The following tables were not found: "
            + ", ".join(missing_tables)
        )

    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        for table in tables_to_export:
            df = pd.read_sql_query(
                f'SELECT * FROM "{table}"',
                conn
            )

            df.to_excel(
                writer,
                sheet_name=table,
                index=False
            )

            print(f"Exported {table}: {len(df):,} rows")

print(f"\nExcel file created: {excel_file.resolve()}")