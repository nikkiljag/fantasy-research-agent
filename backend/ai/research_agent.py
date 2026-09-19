import json
import re

from ai.foundry_local import (
    complete_chat,
)

from services.research import (
    get_database_schema,
    run_research_query,
)


RESEARCH_TABLES = {
    "player_week",
    "league_ownership",
}


def format_schema():
    """
    Give the AI a readable description of the
    database tables it is allowed to use.
    """

    schema = get_database_schema()

    lines = []

    for table_name in RESEARCH_TABLES:

        if table_name not in schema:
            continue

        lines.append(
            f"\nTABLE: {table_name}"
        )

        for column in schema[table_name]:

            lines.append(
                f"- {column['name']} "
                f"({column['type']})"
            )

    return "\n".join(lines)


def extract_sql(response):
    """
    Extract a SELECT or WITH query from a model response.

    Small local models sometimes wrap SQL in explanations
    even when instructed not to.
    """

    response = response.strip()

    # First try markdown code fences
    fenced = re.search(
        r"```(?:sql)?\s*(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE,
    )

    if fenced:
        response = fenced.group(1).strip()

    # Find the first SELECT or WITH statement
    sql_start = re.search(
        r"\b(SELECT|WITH)\b",
        response,
        re.IGNORECASE,
    )

    if not sql_start:
        raise ValueError(
            "The model did not generate a SQL query."
        )

    sql = response[
        sql_start.start():
    ].strip()

    # Remove a trailing markdown fence if one survived
    sql = sql.replace("```", "").strip()

    return sql


def generate_research_sql(question):
    """
    Ask the model to create SQL for the user's question.
    """

    schema = format_schema()

    messages = [
        {
            "role": "system",
            "content": (
                "You write DuckDB SQL for a fantasy football "
                "analytics database.\n\n"

                "IMPORTANT RULES:\n"
                "1. Output ONE SQL query only.\n"
                "2. Do not explain the query.\n"
                "3. Do not write 'SQL:' before the query.\n"
                "4. The first word must be SELECT or WITH.\n"
                "5. Never modify the database.\n"
                "6. Only use columns in the provided schema.\n\n"

                "DATA RULES:\n"
                "- player_week contains NFL performance and usage.\n"
                "- league_ownership contains players currently "
                "rostered in the fantasy league.\n"
                "- A player is available when their sleeper_id "
                "does NOT exist in league_ownership.\n"
                "- offense_pct is offensive snap share from 0 to 1.\n"
                "- For RB opportunity, carries and targets are "
                "important evidence.\n"
            ),
        },
        {
            "role": "user",
            "content": (
                f"DATABASE SCHEMA:\n"
                f"{schema}\n\n"
                f"USER QUESTION:\n"
                f"{question}\n\n"
                "Return only the SQL query."
            ),
        },
    ]

    response = complete_chat(
        messages
    )

    return extract_sql(
        response
    )


def repair_sql(
    question,
    failed_sql,
    error_message,
):
    """
    Give the model one chance to repair an invalid query.
    """

    schema = format_schema()

    messages = [
        {
            "role": "system",
            "content": (
                "You repair DuckDB SQL queries.\n\n"

                "Return ONE corrected SQL query only.\n"
                "The first word must be SELECT or WITH.\n"
                "Do not explain anything.\n"
                "Never modify the database.\n"
                "Only use columns from the provided schema."
            ),
        },
        {
            "role": "user",
            "content": (
                f"DATABASE SCHEMA:\n"
                f"{schema}\n\n"

                f"ORIGINAL QUESTION:\n"
                f"{question}\n\n"

                f"FAILED SQL:\n"
                f"{failed_sql}\n\n"

                f"DATABASE ERROR:\n"
                f"{error_message}\n\n"

                "Return the corrected SQL only."
            ),
        },
    ]

    response = complete_chat(
        messages
    )

    return extract_sql(
        response
    )


def execute_with_retry(
    question,
    sql,
):
    """
    Execute model-generated SQL.

    If it fails, allow the model one repair attempt.
    """

    try:

        results = run_research_query(
            sql
        )

        return sql, results

    except Exception as first_error:

        print(
            "\nInitial SQL failed. "
            "Asking the model to repair it..."
        )

        repaired_sql = repair_sql(
            question,
            sql,
            str(first_error),
        )

        results = run_research_query(
            repaired_sql
        )

        return repaired_sql, results


def explain_results(
    question,
    sql,
    results,
):
    """
    Ask the model to interpret database evidence.
    """

    rows = (
        results
        .head(20)
        .to_dicts()
    )

    evidence = json.dumps(
        rows,
        indent=2,
        default=str,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a fantasy football research analyst. "
                "Explain the supplied database results clearly. "
                "Use only the provided evidence. "
                "Do not invent statistics, injuries, news, "
                "matchups, or player information that is not "
                "present in the results. "
                "Mention useful numbers when supporting your answer."
            ),
        },
        {
            "role": "user",
            "content": (
                f"QUESTION:\n"
                f"{question}\n\n"

                f"SQL USED:\n"
                f"{sql}\n\n"

                f"RESULTS:\n"
                f"{evidence}"
            ),
        },
    ]

    return complete_chat(
        messages
    )


def research(question):
    """
    Complete research cycle:

    question
    -> SQL generation
    -> safe execution
    -> optional SQL repair
    -> evidence-based explanation
    """

    sql = generate_research_sql(
        question
    )

    final_sql, results = (
        execute_with_retry(
            question,
            sql,
        )
    )

    answer = explain_results(
        question,
        final_sql,
        results,
    )

    return {
        "question": question,
        "sql": final_sql,
        "results": results,
        "answer": answer,
    }