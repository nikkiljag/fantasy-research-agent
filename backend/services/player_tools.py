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


# These are logical analytics metrics that the agent is
# allowed to request for sorting.
#
# The important idea is that the AI chooses from these
# reusable concepts instead of writing arbitrary SQL.
ALLOWED_SORT_METRICS = {
    "avg_carries",
    "avg_targets",
    "avg_opportunities",
    "avg_snap_pct",
    "avg_ppr",
}


# ============================================================
# GENERIC PLAYER SEARCH
# ============================================================

def search_players(
    position=None,
    availability="all",
    sort_by=None,
    limit=10,
):
    """
    Generic fantasy-football player research tool.

    The AI can control:
    - position
    - ownership/availability
    - ranking metrics
    - result count

    Multiple sort metrics may be supplied.

    Example:

        search_players(
            position="RB",
            availability="unrostered",
            sort_by=[
                "avg_carries",
                "avg_snap_pct",
            ],
            limit=10,
        )

    This ranks primarily by carries and then uses
    snap share as the secondary ranking criterion.
    """

    # --------------------------------------------------------
    # VALIDATE POSITION
    # --------------------------------------------------------

    if position is not None:

        position = position.upper()

        if position not in ALLOWED_POSITIONS:

            raise ValueError(
                f"Unsupported position: {position}"
            )


    # --------------------------------------------------------
    # VALIDATE AVAILABILITY
    # --------------------------------------------------------

    availability = availability.lower()

    if availability not in ALLOWED_AVAILABILITY:

        raise ValueError(
            f"Unsupported availability: "
            f"{availability}"
        )


    # --------------------------------------------------------
    # VALIDATE SORT METRICS
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

        if metric not in ALLOWED_SORT_METRICS:

            raise ValueError(
                f"Unsupported sort metric: "
                f"{metric}"
            )


    # --------------------------------------------------------
    # VALIDATE LIMIT
    # --------------------------------------------------------

    limit = max(
        1,
        min(
            int(limit),
            50,
        ),
    )


    # --------------------------------------------------------
    # BUILD FILTERS
    # --------------------------------------------------------

    where_conditions = []

    parameters = []


    if position is not None:

        where_conditions.append(
            "pw.position = ?"
        )

        parameters.append(
            position
        )


    if availability == "unrostered":

        where_conditions.append(
            "own.sleeper_id IS NULL"
        )

    elif availability == "rostered":

        where_conditions.append(
            "own.sleeper_id IS NOT NULL"
        )


    if where_conditions:

        where_sql = (
            "WHERE "
            + " AND ".join(
                where_conditions
            )
        )

    else:

        where_sql = ""


    # --------------------------------------------------------
    # BUILD SAFE ORDER BY
    # --------------------------------------------------------

    order_sql = ", ".join(
        f"{metric} DESC"
        for metric in sort_by
    )


    # --------------------------------------------------------
    # QUERY
    # --------------------------------------------------------

    sql = f"""
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

    {where_sql}

    GROUP BY
        pw.sleeper_id,
        pw.name,
        pw.position,
        pw.team

    ORDER BY
        {order_sql}

    LIMIT {limit}
    """


    return query_dataframe(
        sql,
        parameters,
    )


# ============================================================
# BACKWARD-COMPATIBLE WRAPPER
# ============================================================

def find_available_players(
    position,
    sort_by="avg_opportunities",
    limit=10,
):
    """
    Temporary compatibility wrapper for the existing
    Foundry tool agent.

    Eventually the agent will call search_players()
    directly.
    """

    return search_players(
        position=position,
        availability="unrostered",
        sort_by=[
            sort_by
        ],
        limit=limit,
    )