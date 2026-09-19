import polars as pl

from sleeper import (
    get_all_players,
    get_league_users,
    get_rosters,
)


def get_league_ownership(league_id):
    """
    Build a table containing every rostered player
    and team defense in a Sleeper league.

    This allows us to determine:

    - who owns a player
    - which roster they belong to
    - whether they are starting or benched
    - which manager owns the roster
    """

    rosters = get_rosters(
        league_id
    )

    users = get_league_users(
        league_id
    )

    players = get_all_players()

    # --------------------------------------------------
    # Manager lookup
    # --------------------------------------------------

    user_lookup = {
        user["user_id"]: user
        for user in users
    }

    rows = []

    # --------------------------------------------------
    # Build one row per rostered entity
    # --------------------------------------------------

    for roster in rosters:

        roster_id = roster.get(
            "roster_id"
        )

        owner_id = roster.get(
            "owner_id"
        )

        starters = set(
            roster.get("starters") or []
        )

        roster_players = (
            roster.get("players") or []
        )

        settings = (
            roster.get("settings") or {}
        )

        manager = user_lookup.get(
            owner_id,
            {},
        )

        metadata = (
            manager.get("metadata") or {}
        )

        display_name = manager.get(
            "display_name"
        )

        username = manager.get(
            "username"
        )

        team_name = (
            metadata.get("team_name")
            or display_name
            or username
            or f"Roster {roster_id}"
        )

        # ----------------------------------------------
        # Each player on this roster
        # ----------------------------------------------

        for sleeper_id in roster_players:

            if sleeper_id.isdigit():

                player = players.get(
                    sleeper_id,
                    {},
                )

                name = player.get(
                    "full_name",
                    sleeper_id,
                )

                position = player.get(
                    "position"
                )

                nfl_team = player.get(
                    "team"
                )

                entity_type = "player"

            else:

                name = (
                    f"{sleeper_id} D/ST"
                )

                position = "DEF"

                nfl_team = sleeper_id

                entity_type = (
                    "team_defense"
                )

            rows.append({
                "league_id": str(
                    league_id
                ),

                "roster_id": roster_id,

                "owner_id": owner_id,

                "manager_username": (
                    username
                ),

                "manager_display_name": (
                    display_name
                ),

                "fantasy_team_name": (
                    team_name
                ),

                "wins": settings.get(
                    "wins",
                    0,
                ),

                "losses": settings.get(
                    "losses",
                    0,
                ),

                "sleeper_id": (
                    str(sleeper_id)
                ),

                "name": name,

                "position": position,

                "nfl_team": nfl_team,

                "entity_type": (
                    entity_type
                ),

                "lineup_status": (
                    "starter"
                    if sleeper_id in starters
                    else "bench"
                ),
            })

    return pl.DataFrame(rows)