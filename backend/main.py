from database import (
    list_tables,
    query_dataframe,
    save_league_nfl_data,
    save_league_ownership,
    save_team_data,
)

from nflverse import (
    get_all_snap_counts,
    get_all_weekly_stats,
    get_all_weekly_status,
    get_player_identity_table,
)

from services.fantasy_data import (
    get_team_context,
)

from services.league_data import (
    get_league_ownership,
)

from services.player_week import (
    build_player_week_table,
)


username = input(
    "Enter your Sleeper username: "
)


# ==================================================
# USER TEAM
# ==================================================

try:

    team = get_team_context(
        username
    )

except ValueError as error:

    print(
        f"\nError: {error}"
    )

    raise SystemExit


league_id = (
    team["league"]["league_id"]
)


# ==================================================
# LEAGUE OWNERSHIP
# ==================================================

print(
    "\nLoading league ownership..."
)

league_ownership = (
    get_league_ownership(
        league_id
    )
)

print(
    f"Rostered entities: "
    f"{league_ownership.height}"
)


# ==================================================
# NFL PLAYER IDENTITIES
# ==================================================

print(
    "\nLoading NFL player identities..."
)

player_identity = (
    get_player_identity_table()
)

print(
    f"Mapped NFL players: "
    f"{player_identity.height}"
)


# ==================================================
# LEAGUE-WIDE NFL DATA
# ==================================================

print(
    "\nLoading weekly NFL stats..."
)

all_weekly_stats = (
    get_all_weekly_stats(
        season=2026
    )
)

print(
    f"Weekly stat rows: "
    f"{all_weekly_stats.height}"
)


print(
    "\nLoading NFL snap counts..."
)

all_snap_counts = (
    get_all_snap_counts(
        season=2026
    )
)

print(
    f"Snap-count rows: "
    f"{all_snap_counts.height}"
)


print(
    "\nLoading weekly NFL roster status..."
)

all_weekly_status = (
    get_all_weekly_status(
        season=2026
    )
)

print(
    f"Weekly status rows: "
    f"{all_weekly_status.height}"
)


# ==================================================
# UNIFIED PLAYER-WEEK TABLE
# ==================================================

print(
    "\nBuilding unified player-week table..."
)

player_week = build_player_week_table(
    all_weekly_stats,
    all_snap_counts,
    all_weekly_status,
)

print(
    f"Player-week rows: "
    f"{player_week.height}"
)


# ==================================================
# SAVE EVERYTHING TO DUCKDB
# ==================================================

print(
    "\nSaving data to DuckDB..."
)

save_team_data(
    team
)

save_league_ownership(
    league_ownership
)

save_league_nfl_data(
    player_identity,
    all_weekly_stats,
    all_snap_counts,
    all_weekly_status,
    player_week,
)

print(
    "Database updated successfully."
)

print(
    "Database tables:",
    list_tables(),
)


# ==================================================
# USAGE-BASED WAIVER QUERY
# ==================================================

print(
    "\n=============================="
)

print(
    "USAGE-BASED WAIVER TEST"
)

print(
    "=============================="
)


waiver_results = query_dataframe(
    """
    SELECT
        pw.name,
        pw.position,
        pw.team,

        COUNT(*) AS games,

        ROUND(
            AVG(
                COALESCE(pw.targets, 0)
                +
                COALESCE(pw.carries, 0)
            ),
            2
        ) AS avg_opportunities,

        ROUND(
            AVG(pw.offense_pct) * 100,
            1
        ) AS avg_snap_pct,

        ROUND(
            AVG(pw.fantasy_points_ppr),
            2
        ) AS avg_ppr,

        SUM(
            COALESCE(pw.targets, 0)
        ) AS total_targets,

        SUM(
            COALESCE(pw.carries, 0)
        ) AS total_carries

    FROM player_week AS pw

    LEFT JOIN league_ownership AS own
        ON pw.sleeper_id = own.sleeper_id

    WHERE
        own.sleeper_id IS NULL

        AND pw.position IN (
            'RB',
            'WR',
            'TE'
        )

    GROUP BY
        pw.sleeper_id,
        pw.name,
        pw.position,
        pw.team

    ORDER BY
        avg_opportunities DESC,
        avg_snap_pct DESC

    LIMIT 20
    """
)


print(
    "\nTop available players by usage:\n"
)

print(
    waiver_results
)