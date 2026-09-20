from database import query_dataframe


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


ALLOWED_METRICS = {
    "games",
    "avg_carries",
    "avg_targets",
    "avg_opportunities",
    "avg_snap_pct",
    "avg_ppr",
}


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
    - league ownership filtering
    - multiple ranking metrics
    - arbitrary validated metric filters
    - recent-week windows
    """

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
            f"Unsupported availability: {availability}"
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
                f"Unsupported sort metric: {metric}"
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
                f"Unsupported filter metric: {metric}"
            )


        if operator not in ALLOWED_OPERATORS:

            raise ValueError(
                f"Unsupported filter operator: {operator}"
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
                "last_n_weeks must be between 1 and 18."
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
    # BUILD BASE ROW FILTERS
    # ========================================================

    base_conditions = []

    parameters = []


    if position is not None:

        base_conditions.append(
            "pw.position = ?"
        )

        parameters.append(
            position
        )


    if availability == "unrostered":

        base_conditions.append(
            "own.sleeper_id IS NULL"
        )

    elif availability == "rostered":

        base_conditions.append(
            "own.sleeper_id IS NOT NULL"
        )


    if last_n_weeks is not None:

        base_conditions.append(
            """
            pw.week >= (
                SELECT MAX(week)
                FROM player_week
            ) - ?
            """
        )

        parameters.append(
            last_n_weeks - 1
        )


    if base_conditions:

        base_where_sql = (
            "WHERE "
            + " AND ".join(
                base_conditions
            )
        )

    else:

        base_where_sql = ""


    # ========================================================
    # BUILD AGGREGATE FILTERS
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
        f"{metric} DESC"
        for metric in sort_by
    )


    # ========================================================
    # QUERY
    # ========================================================

    sql = f"""
    WITH aggregated AS (

        SELECT
            pw.sleeper_id,
            pw.name,
            pw.position,
            pw.team,

            COUNT(*) AS games,

            ROUND(
                AVG(
                    COALESCE(
                        pw.carries,
                        0
                    )
                ),
                2
            ) AS avg_carries,

            ROUND(
                AVG(
                    COALESCE(
                        pw.targets,
                        0
                    )
                ),
                2
            ) AS avg_targets,

            ROUND(
                AVG(
                    COALESCE(
                        pw.carries,
                        0
                    )
                    +
                    COALESCE(
                        pw.targets,
                        0
                    )
                ),
                2
            ) AS avg_opportunities,

            ROUND(
                AVG(
                    pw.offense_pct
                ) * 100,
                1
            ) AS avg_snap_pct,

            ROUND(
                AVG(
                    pw.fantasy_points_ppr
                ),
                2
            ) AS avg_ppr

        FROM player_week AS pw

        LEFT JOIN league_ownership AS own
            ON pw.sleeper_id = own.sleeper_id

        {base_where_sql}

        GROUP BY
            pw.sleeper_id,
            pw.name,
            pw.position,
            pw.team
    )

    SELECT *
    FROM aggregated

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
# OLD COMPATIBILITY WRAPPER
# ============================================================

def find_available_players(
    position,
    sort_by="avg_opportunities",
    limit=10,
):
    """
    Compatibility wrapper retained temporarily.
    """

    return search_players(
        position=position,
        availability="unrostered",
        sort_by=[
            sort_by
        ],
        limit=limit,
    )