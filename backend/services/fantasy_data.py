from sleeper import (
    get_all_players,
    get_leagues,
    get_rosters,
    get_user,
    get_user_roster,
)

from nflverse import (
    build_roster_mapping,
    get_roster_snap_counts,
    get_roster_weekly_stats,
    get_roster_weekly_status,
)


def get_team_context(username, season=2026):
    """
    Build a combined fantasy + NFL data package
    for a Sleeper user's team.
    """

    # --------------------------------------------------
    # Sleeper user
    # --------------------------------------------------

    user = get_user(username)

    if not user:
        raise ValueError("Sleeper user not found.")

    user_id = user["user_id"]


    # --------------------------------------------------
    # Sleeper league
    # --------------------------------------------------

    leagues = get_leagues(user_id, season)

    if not leagues:
        raise ValueError(f"No Sleeper leagues found for {season}.")

    # Temporary:
    # use first league until multi-league selection is added
    league = leagues[0]

    league_id = league["league_id"]


    # --------------------------------------------------
    # Sleeper roster
    # --------------------------------------------------

    rosters = get_rosters(league_id)

    roster = get_user_roster(
        rosters,
        user_id
    )

    if roster is None:
        raise ValueError("Could not find user's roster.")


    # --------------------------------------------------
    # Sleeper player metadata
    # --------------------------------------------------

    sleeper_players = get_all_players()


    # --------------------------------------------------
    # Sleeper -> NFL identity mapping
    # --------------------------------------------------

    roster_mapping = build_roster_mapping(
        roster["players"]
    )


    # --------------------------------------------------
    # NFL data
    # --------------------------------------------------

    weekly_stats = get_roster_weekly_stats(
        roster_mapping,
        season
    )

    snap_counts = get_roster_snap_counts(
        roster_mapping,
        season
    )

    weekly_status = get_roster_weekly_status(
        roster_mapping,
        season
    )


    # --------------------------------------------------
    # Starting lineup / bench
    # --------------------------------------------------

    starters = roster["starters"]

    bench = [
        player_id
        for player_id in roster["players"]
        if player_id not in starters
    ]


    # --------------------------------------------------
    # Combined result
    # --------------------------------------------------

    return {
        "user": {
            "user_id": user_id,
            "username": user.get("username"),
            "display_name": user.get("display_name"),
        },

        "league": {
            "league_id": league_id,
            "name": league["name"],
            "season": season,
            "total_rosters": league["total_rosters"],
            "roster_positions": league["roster_positions"],
            "scoring_settings": league["scoring_settings"],
        },

        "roster": {
            "roster_id": roster["roster_id"],
            "wins": roster["settings"].get("wins", 0),
            "losses": roster["settings"].get("losses", 0),
            "players": roster["players"],
            "starters": starters,
            "bench": bench,
        },

        "sleeper_players": sleeper_players,

        "roster_mapping": roster_mapping,
        "weekly_stats": weekly_stats,
        "snap_counts": snap_counts,
        "weekly_status": weekly_status,
    }