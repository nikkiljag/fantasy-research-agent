from database import (
    list_tables,
    query_dataframe,
    save_league_ownership,
    save_team_data,
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
# LEAGUE-WIDE OWNERSHIP
# ==================================================

print(
    "\nLoading entire league ownership..."
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

print(
    "Database updated successfully."
)

print(
    "Database tables:",
    list_tables(),
)


# ==================================================
# LEAGUE SUMMARY
# ==================================================

print(
    "\n=============================="
)

print(
    "LEAGUE SUMMARY"
)

print(
    "=============================="
)

print(
    f"\nLeague: "
    f"{team['league']['name']}"
)

print(
    f"Teams: "
    f"{team['league']['total_rosters']}"
)

print(
    f"Your record: "
    f"{team['roster']['wins']}-"
    f"{team['roster']['losses']}"
)


# ==================================================
# OWNERSHIP DATABASE TEST
# ==================================================

ownership_summary = query_dataframe(
    """
    SELECT
        roster_id,
        fantasy_team_name,
        manager_display_name,
        wins,
        losses,
        COUNT(*) AS roster_size
    FROM league_ownership
    GROUP BY
        roster_id,
        fantasy_team_name,
        manager_display_name,
        wins,
        losses
    ORDER BY
        roster_id
    """
)

print(
    "\nLeague teams stored in DuckDB:\n"
)

print(
    ownership_summary
)