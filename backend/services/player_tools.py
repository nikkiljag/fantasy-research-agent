from database import query_dataframe

from services.schedule_data import (
    get_latest_completed_week,
)


# ============================================================
# ALLOWED INPUTS
# ============================================================

ALLOWED_POSITIONS = {
    "QB",
    "RB",
    "WR",
    "TE",
}


ALLOWED_AVAILABILITY = {
    "unrostered",
    "rostered",
    "all",
}


BASIC_METRICS = {
    "games",
    "avg_carries",
    "avg_targets",
    "avg_opportunities",
    "avg_snap_pct",
    "avg_ppr",
}


TREND_METRICS = {
    "carries_trend",
    "targets_trend",
    "opportunities_trend",
    "snap_pct_trend",
    "ppr_trend",
}


ALLOWED_METRICS = (
    BASIC_METRICS
    | TREND_METRICS
)


ALLOWED_OPERATORS = {
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "eq": "=",
}


# ============================================================
# GENERIC PLAYER SEARCH
# ============================================================

def search_players(
    position=None,
    availability="all",
    sort_by=None,
    filters=None,
    last_n_weeks=None,
    limit=10,
):
    """
    Generic fantasy-football research engine.

    Supports:
    - position filtering
    - ownership filtering
    - multiple ranking metrics
    - numerical filters
    - recent-week windows
    - usage and fantasy-point trends

    Important behavior:

    1. Without last_n_weeks:
       Normal averages may include the newest available
       player data, including data from the current week.

    2. Trend calculations:
       Only use fully completed NFL weeks.

    3. With last_n_weeks:
       The requested window refers to the most recent
       fully completed NFL weeks.

    4. Trend analysis requires at least two completed weeks.
    """

    # --------------------------------------------------------
    # LATEST COMPLETED NFL WEEK
    # --------------------------------------------------------

    latest_completed_week = (
        get_latest_completed_week()
    )


    # --------------------------------------------------------
    # POSITION
    # --------------------------------------------------------

    if position is not None:

        position = position.upper()

        if position not in ALLOWED_POSITIONS:

            raise ValueError(
                f"Unsupported position: {position}"
            )


    # --------------------------------------------------------
    # AVAILABILITY
    # --------------------------------------------------------

    availability = availability.lower()

    if availability not in ALLOWED_AVAILABILITY:

        raise ValueError(
            f"Unsupported availability: "
            f"{availability}"
        )


    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    if sort_by is None:

        sort_by = [
            "avg_opportunities"
        ]

    elif isinstance(
        sort_by,
        str,
    ):

        sort_by = [
            sort_by
        ]


    for metric in sort_by:

        if metric not in ALLOWED_METRICS:

            raise ValueError(
                f"Unsupported sort metric: "
                f"{metric}"
            )


    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    if filters is None:

        filters = []


    validated_filters = []

    for item in filters:

        metric = item.get(
            "metric"
        )

        operator = item.get(
            "operator"
        )

        value = item.get(
            "value"
        )


        if metric not in ALLOWED_METRICS:

            raise ValueError(
                f"Unsupported filter metric: "
                f"{metric}"
            )


        if operator not in ALLOWED_OPERATORS:

            raise ValueError(
                f"Unsupported filter operator: "
                f"{operator}"
            )


        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            raise ValueError(
                f"Invalid filter value: {value}"
            )


        validated_filters.append({
            "metric": metric,
            "operator": operator,
            "value": value,
        })


    # --------------------------------------------------------
    # WEEK WINDOW
    # --------------------------------------------------------

    if last_n_weeks is not None:

        last_n_weeks = int(
            last_n_weeks
        )

        if (
            last_n_weeks < 1
            or last_n_weeks > 18
        ):

            raise ValueError(
                "last_n_weeks must be "
                "between 1 and 18."
            )


        if latest_completed_week is None:

            raise ValueError(
                "No fully completed NFL weeks "
                "are available yet."
            )


    # --------------------------------------------------------
    # CHECK WHETHER TREND DATA IS BEING REQUESTED
    # --------------------------------------------------------

    requested_metrics = set(
        sort_by
    )

    requested_metrics.update(
        item["metric"]
        for item in validated_filters
    )


    trend_requested = bool(
        requested_metrics
        & TREND_METRICS
    )


    if trend_requested:

        if latest_completed_week is None:

            raise ValueError(
                "Trend analysis is not available "
                "because no NFL week has fully "
                "completed yet."
            )


        if last_n_weeks is None:

            completed_weeks_available = (
                latest_completed_week
            )

        else:

            completed_weeks_available = min(
                last_n_weeks,
                latest_completed_week,
            )


        if completed_weeks_available < 2:

            raise ValueError(
                "Trend analysis requires at least "
                "two fully completed NFL weeks. "
                f"The latest fully completed week "
                f"is Week {latest_completed_week}."
            )


    # --------------------------------------------------------
    # LIMIT
    # --------------------------------------------------------

    limit = max(
        1,
        min(
            int(limit),
            50,
        ),
    )


    # ========================================================
    # PLAYER / OWNERSHIP FILTERS
    # ========================================================

    eligibility_conditions = []

    parameters = []


    if position is not None:

        eligibility_conditions.append(
            "pw.position = ?"
        )

        parameters.append(
            position
        )


    if availability == "unrostered":

        eligibility_conditions.append(
            "own.sleeper_id IS NULL"
        )

    elif availability == "rostered":

        eligibility_conditions.append(
            "own.sleeper_id IS NOT NULL"
        )


    if eligibility_conditions:

        eligibility_where_sql = (
            "WHERE "
            + " AND ".join(
                eligibility_conditions
            )
        )

    else:

        eligibility_where_sql = ""


    # ========================================================
    # AVERAGE STAT WINDOW
    # ========================================================

    average_conditions = []


    # If the user explicitly asks for the last N weeks,
    # use only fully completed weeks for the whole request.
    if last_n_weeks is not None:

        start_week = max(
            1,
            latest_completed_week
            - last_n_weeks
            + 1,
        )

        average_conditions.append(
            "week >= ?"
        )

        parameters.append(
            start_week
        )

        average_conditions.append(
            "week <= ?"
        )

        parameters.append(
            latest_completed_week
        )


    if average_conditions:

        average_where_sql = (
            "WHERE "
            + " AND ".join(
                average_conditions
            )
        )

    else:

        average_where_sql = ""


    # ========================================================
    # TREND WINDOW
    # ========================================================

    trend_conditions = []


    if latest_completed_week is None:

        # Deliberately produce no trend-source rows.
        trend_conditions.append(
            "1 = 0"
        )

    else:

        trend_conditions.append(
            "week <= ?"
        )

        parameters.append(
            latest_completed_week
        )


        if last_n_weeks is not None:

            trend_start_week = max(
                1,
                latest_completed_week
                - last_n_weeks
                + 1,
            )

            trend_conditions.append(
                "week >= ?"
            )

            parameters.append(
                trend_start_week
            )


    trend_where_sql = (
        "WHERE "
        + " AND ".join(
            trend_conditions
        )
    )


    # ========================================================
    # RESULT FILTERS
    # ========================================================

    result_conditions = []


    for item in validated_filters:

        sql_operator = (
            ALLOWED_OPERATORS[
                item["operator"]
            ]
        )

        result_conditions.append(
            f"{item['metric']} "
            f"{sql_operator} ?"
        )

        parameters.append(
            item["value"]
        )


    if result_conditions:

        result_where_sql = (
            "WHERE "
            + " AND ".join(
                result_conditions
            )
        )

    else:

        result_where_sql = ""


    # ========================================================
    # SAFE ORDER BY
    # ========================================================

    order_sql = ", ".join(
        f"{metric} DESC NULLS LAST"
        for metric in sort_by
    )


    # ========================================================
    # QUERY
    # ========================================================

    sql = f"""
    WITH eligible AS (

        SELECT
            pw.*

        FROM player_week AS pw

        LEFT JOIN league_ownership AS own
            ON pw.sleeper_id = own.sleeper_id

        {eligibility_where_sql}
    ),


    average_source AS (

        SELECT *

        FROM eligible

        {average_where_sql}
    ),


    trend_source AS (

        SELECT *

        FROM eligible

        {trend_where_sql}
    ),


    averages AS (

        SELECT
            sleeper_id,
            name,
            position,
            team,

            COUNT(*) AS games,

            ROUND(
                AVG(
                    COALESCE(
                        carries,
                        0
                    )
                ),
                2
            ) AS avg_carries,

            ROUND(
                AVG(
                    COALESCE(
                        targets,
                        0
                    )
                ),
                2
            ) AS avg_targets,

            ROUND(
                AVG(
                    COALESCE(
                        carries,
                        0
                    )
                    +
                    COALESCE(
                        targets,
                        0
                    )
                ),
                2
            ) AS avg_opportunities,

            ROUND(
                AVG(
                    offense_pct
                ) * 100,
                1
            ) AS avg_snap_pct,

            ROUND(
                AVG(
                    fantasy_points_ppr
                ),
                2
            ) AS avg_ppr

        FROM average_source

        GROUP BY
            sleeper_id,
            name,
            position,
            team
    ),


    trends AS (

        SELECT
            sleeper_id,

            CASE
                WHEN COUNT(
                    DISTINCT week
                ) >= 2
                THEN ROUND(
                    REGR_SLOPE(
                        COALESCE(
                            carries,
                            0
                        ),
                        week
                    ),
                    2
                )
                ELSE NULL
            END AS carries_trend,


            CASE
                WHEN COUNT(
                    DISTINCT week
                ) >= 2
                THEN ROUND(
                    REGR_SLOPE(
                        COALESCE(
                            targets,
                            0
                        ),
                        week
                    ),
                    2
                )
                ELSE NULL
            END AS targets_trend,


            CASE
                WHEN COUNT(
                    DISTINCT week
                ) >= 2
                THEN ROUND(
                    REGR_SLOPE(
                        COALESCE(
                            carries,
                            0
                        )
                        +
                        COALESCE(
                            targets,
                            0
                        ),
                        week
                    ),
                    2
                )
                ELSE NULL
            END AS opportunities_trend,


            CASE
                WHEN COUNT(
                    DISTINCT CASE
                        WHEN offense_pct
                        IS NOT NULL
                        THEN week
                    END
                ) >= 2
                THEN ROUND(
                    REGR_SLOPE(
                        offense_pct * 100,
                        week
                    ),
                    2
                )
                ELSE NULL
            END AS snap_pct_trend,


            CASE
                WHEN COUNT(
                    DISTINCT CASE
                        WHEN fantasy_points_ppr
                        IS NOT NULL
                        THEN week
                    END
                ) >= 2
                THEN ROUND(
                    REGR_SLOPE(
                        fantasy_points_ppr,
                        week
                    ),
                    2
                )
                ELSE NULL
            END AS ppr_trend

        FROM trend_source

        GROUP BY
            sleeper_id
    ),


    combined AS (

        SELECT
            a.sleeper_id,
            a.name,
            a.position,
            a.team,

            a.games,
            a.avg_carries,
            a.avg_targets,
            a.avg_opportunities,
            a.avg_snap_pct,
            a.avg_ppr,

            t.carries_trend,
            t.targets_trend,
            t.opportunities_trend,
            t.snap_pct_trend,
            t.ppr_trend

        FROM averages AS a

        LEFT JOIN trends AS t
            ON
                a.sleeper_id
                =
                t.sleeper_id
    )


    SELECT *

    FROM combined

    {result_where_sql}

    ORDER BY
        {order_sql}

    LIMIT {limit}
    """


    return query_dataframe(
        sql,
        parameters,
    )


# ============================================================
# COMPATIBILITY WRAPPER
# ============================================================

def find_available_players(
    position,
    sort_by="avg_opportunities",
    limit=10,
):
    """
    Temporary compatibility wrapper for older code.
    """

    return search_players(
        position=position,
        availability="unrostered",
        sort_by=[
            sort_by
        ],
        limit=limit,
    )