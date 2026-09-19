import polars as pl


def build_player_week_table(
    weekly_stats,
    snap_counts,
    weekly_status,
):
    """
    Build one unified row per player per NFL week.

    Weekly player statistics form the base table.
    Snap counts and NFL roster status are attached
    when available.
    """

    # Keep the most useful snap fields for now
    snap_columns = [
        column
        for column in [
            "sleeper_id",
            "week",
            "offense_snaps",
            "offense_pct",
            "st_snaps",
            "st_pct",
        ]
        if column in snap_counts.columns
    ]

    snaps = (
        snap_counts
        .select(snap_columns)
        .unique(
            subset=[
                "sleeper_id",
                "week",
            ]
        )
    )

    # Keep useful weekly status information
    status_columns = [
        column
        for column in [
            "sleeper_id",
            "week",
            "status",
            "status_description_abbr",
        ]
        if column in weekly_status.columns
    ]

    statuses = (
        weekly_status
        .select(status_columns)
        .unique(
            subset=[
                "sleeper_id",
                "week",
            ]
        )
    )

    player_week = (
        weekly_stats
        .join(
            snaps,
            on=[
                "sleeper_id",
                "week",
            ],
            how="left",
        )
        .join(
            statuses,
            on=[
                "sleeper_id",
                "week",
            ],
            how="left",
        )
    )

    return player_week.sort([
        "week",
        "name",
    ])