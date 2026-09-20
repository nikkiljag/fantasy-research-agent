from database import query_dataframe


ALLOWED_POSITIONS = {
    "QB",
    "RB",
    "WR",
    "TE",
}


ALLOWED_SORT_METRICS = {
    "avg_carries",
    "avg_targets",
    "avg_opportunities",
    "avg_snap_pct",
    "avg_ppr",
}


def find_available_players(
    position,
    sort_by="avg_opportunities",
    limit=10,
):
    """
    Find unrostered fantasy players using
    league ownership and NFL usage data.

    This is a deterministic analytics tool
    intended for use by the AI research agent.
    """

    position = position.upper()

    if position not in ALLOWED_POSITIONS:
        raise ValueError(
            f"Unsupported position: {position}"
        )

    if sort_by not in ALLOWED_SORT_METRICS:
        raise ValueError(
            f"Unsupported sort metric: {sort_by}"
        )

    limit = max(
        1,
        min(int(limit), 50),
    )

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

    WHERE
        pw.position = ?

        AND own.sleeper_id IS NULL

    GROUP BY
        pw.sleeper_id,
        pw.name,
        pw.position,
        pw.team

    ORDER BY
        {sort_by} DESC

    LIMIT {limit}
    """

    return query_dataframe(
        sql,
        [position],
    )