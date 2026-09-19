from pathlib import Path

import duckdb


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

    The table is replaced each time so our local
    database stays synchronized with the latest data.
    """

    temporary_name = (
        f"temp_{table_name}"
    )

    connection.register(
        temporary_name,
        dataframe
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
    Save the main structured datasets from a team context
    into the local DuckDB database.
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
    Return the tables currently stored in DuckDB.
    """

    connection = get_connection()

    try:

        result = connection.execute(
            """
            SHOW TABLES
            """
        ).fetchall()

        return [
            row[0]
            for row in result
        ]

    finally:

        connection.close()