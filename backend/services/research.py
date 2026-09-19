from database import (
    get_connection,
    query_dataframe,
)


def get_database_schema():
    """
    Return the tables and columns available to the
    research/AI layer.

    This gives the future agent a map of the database.
    """

    connection = get_connection()

    try:
        tables = connection.execute(
            "SHOW TABLES"
        ).fetchall()

        schema = {}

        for table_row in tables:
            table_name = table_row[0]

            columns = connection.execute(
                f"DESCRIBE {table_name}"
            ).fetchall()

            schema[table_name] = [
                {
                    "name": column[0],
                    "type": column[1],
                }
                for column in columns
            ]

        return schema

    finally:
        connection.close()


def run_research_query(sql):
    """
    Execute a read-only analytical SQL query.

    The future AI agent will use this tool to perform
    calculations dynamically instead of relying on
    hundreds of hard-coded fantasy functions.
    """

    cleaned_sql = sql.strip()

    if not cleaned_sql:
        raise ValueError(
            "SQL query cannot be empty."
        )

    first_word = (
        cleaned_sql
        .split()[0]
        .upper()
    )

    allowed_starts = {
        "SELECT",
        "WITH",
    }

    if first_word not in allowed_starts:
        raise ValueError(
            "Only read-only SELECT queries are allowed."
        )

    blocked_keywords = [
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "DROP ",
        "CREATE ",
        "ALTER ",
        "TRUNCATE ",
        "COPY ",
        "ATTACH ",
        "DETACH ",
    ]

    upper_sql = cleaned_sql.upper()

    for keyword in blocked_keywords:
        if keyword in upper_sql:
            raise ValueError(
                f"Blocked SQL operation: {keyword.strip()}"
            )

    return query_dataframe(
        cleaned_sql
    )