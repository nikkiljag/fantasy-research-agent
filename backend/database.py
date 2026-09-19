from pathlib import Path

import duckdb
import polars as pl


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_DIR = PROJECT_ROOT / "data" / "database"
DATABASE_FILE = DATABASE_DIR / "fantasy.duckdb"


def get_connection():
    """
    Open a connection to the local DuckDB database.
    """

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return duckdb.connect(
        str(DATABASE_FILE)
    )


def save_dataframe(
    connection,
    table_name,
    dataframe,
):
    """
    Save a Polars DataFrame into DuckDB.

    The table is replaced each time so local data
    stays synchronized with the latest source data.
    """

    temporary_name = f"temp_{table_name}"

    connection.register(
        temporary_name,
        dataframe,
    )

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE {table_name}
        AS
        SELECT *
        FROM {temporary_name}
        """
    )

    connection.unregister(
        temporary_name
    )


def save_team_data(team):
    """
    Save the main structured team datasets
    into DuckDB.
    """

    connection = get_connection()

    try:

        save_dataframe(
            connection,
            "roster_mapping",
            team["roster_mapping"],
        )

        save_dataframe(
            connection,
            "weekly_stats",
            team["weekly_stats"],
        )

        save_dataframe(
            connection,
            "snap_counts",
            team["snap_counts"],
        )

        save_dataframe(
            connection,
            "weekly_status",
            team["weekly_status"],
        )

    finally:
        connection.close()


def list_tables():
    """
    Return all tables currently stored in DuckDB.
    """

    connection = get_connection()

    try:

        result = connection.execute(
            "SHOW TABLES"
        ).fetchall()

        return [
            row[0]
            for row in result
        ]

    finally:
        connection.close()


def query_dataframe(sql, parameters=None):
    """
    Run a read query against DuckDB and return
    the result as a Polars DataFrame.
    """

    connection = get_connection()

    try:

        if parameters:
            result = connection.execute(
                sql,
                parameters,
            )
        else:
            result = connection.execute(sql)

        arrow_table = (
            result.fetch_arrow_table()
        )

        return pl.from_arrow(
            arrow_table
        )

    finally:
        connection.close()