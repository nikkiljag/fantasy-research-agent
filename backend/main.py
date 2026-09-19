from database import (
    list_tables,
    query_dataframe,
    save_league_nfl_data,
    save_league_ownership,
    save_team_data,
)

from nflverse import (
    get_all_weekly_stats,
    get_player_identity_table,
)

from services.fantasy_data import (
    get_team_context,
)

from services.league_data import (
    get_league_ownership,
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
    f"Rostered entities found: "
    f"{league_ownership.height}"
)


# ==================================================
# LEAGUE-WIDE NFL DATA
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


print(
    "\nLoading league-wide 2026 NFL stats..."
)

all_weekly_stats = (
    get_all_weekly_stats(
        season=2026
    )
)

print(
    f"Weekly NFL stat rows: "
    f"{all_weekly_stats.height}"
)


# ==================================================
# SAVE TO DUCKDB
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
)

print(
    "Database updated successfully."
)

print(
    "Database tables:",
    list_tables(),
)


# ==================================================
# AVAILABLE PLAYER TEST
# ==================================================

print(
    "\n=============================="
)

print(
    "AVAILABLE PLAYER TEST"
)

print(
    "=============================="
)


available_players = query_dataframe(
    """
    SELECT
        s.name,
        s.position,
        s.team,

        COUNT(*) AS games,

        ROUND(
            AVG(s.fantasy_points_ppr),
            2
        ) AS avg_ppr,

        SUM(s.targets) AS targets,

        SUM(s.carries) AS carries

    FROM all_weekly_stats AS s

    LEFT JOIN league_ownership AS o
        ON s.sleeper_id = o.sleeper_id

    WHERE
        o.sleeper_id IS NULL

        AND s.position IN (
            'QB',
            'RB',
            'WR',
            'TE'
        )

    GROUP BY
        s.sleeper_id,
        s.name,
        s.position,
        s.team

    ORDER BY
        avg_ppr DESC

    LIMIT 20
    """
)

print(
    "\nTop available players by average PPR:\n"
)

print(
    available_players
)