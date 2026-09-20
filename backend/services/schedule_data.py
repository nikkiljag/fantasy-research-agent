from database import query_dataframe


def get_latest_completed_week():
    """
    Return the most recent fully completed
    NFL regular-season week.

    A week counts as completed only when every
    scheduled regular-season game has a result.
    """

    result = query_dataframe(
        """
        SELECT
            MAX(week) AS latest_completed_week

        FROM (
            SELECT
                week

            FROM nfl_schedule

            WHERE game_type = ?

            GROUP BY week

            HAVING
                COUNT(*) = COUNT(result)
        )
        """,
        ["REG"],
    )


    if result.is_empty():
        return None


    week = result[
        "latest_completed_week"
    ][0]


    if week is None:
        return None


    return int(
        week
    )