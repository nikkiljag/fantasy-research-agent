from pathlib import Path

import duckdb
import polars as pl


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_DIR = (
    PROJECT_ROOT
    / "data"
    / "database"
)

DATABASE_FILE = (
    DATABASE_DIR
    / "fantasy.duckdb"
)


def get_connection():
    """
    Open the local DuckDB database.
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
    """

    temporary_name = (
        f"temp_{table_name}"
    )

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
    Save datasets associated with the user's team.
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


def save_league_ownership(
    league_ownership,
):
    """
    Save league-wide fantasy ownership data.
    """

    connection = get_connection()

    try:

        save_dataframe(
            connection,
            "league_ownership",
            league_ownership,
        )

    finally:

        connection.close()


def list_tables():
    """
    Return all DuckDB table names.
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


def query_dataframe(
    sql,
    parameters=None,
):
    """
    Execute a SQL query and return
    a Polars DataFrame.
    """

    connection = get_connection()

    try:

        if parameters:

            result = connection.execute(
                sql,
                parameters,
            )

        else:

            result = connection.execute(
                sql
            )

        arrow_table = (
            result.fetch_arrow_table()
        )

        return pl.from_arrow(
            arrow_table
        )

    finally:

        connection.close()