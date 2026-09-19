import polars as pl

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

def build_player_contexts(
    roster,
    sleeper_players,
    roster_mapping,
    weekly_stats,
    snap_counts,
    weekly_status,
):
    """
    Combine fantasy roster information and NFL data into
    one organized record for each rostered player.
    """

    mapping_lookup = {}

    for row in roster_mapping.iter_rows(named=True):
        mapping_lookup[str(row["sleeper_id"])] = row

    starters = set(roster["starters"])

    player_contexts = []

    for sleeper_id in roster["players"]:

        sleeper_info = sleeper_players.get(sleeper_id, {})

        # --------------------------------------------------
        # Team defenses
        # --------------------------------------------------

        if not sleeper_id.isdigit():
            player_contexts.append({
                "sleeper_id": sleeper_id,
                "gsis_id": None,
                "name": f"{sleeper_id} D/ST",
                "position": "DEF",
                "team": sleeper_id,
                "entity_type": "team_defense",
                "lineup_status": (
                    "starter"
                    if sleeper_id in starters
                    else "bench"
                ),
                "weekly_stats": [],
                "snap_counts": [],
                "weekly_status": [],
            })

            continue

        # --------------------------------------------------
        # Individual players
        # --------------------------------------------------

        mapping = mapping_lookup.get(sleeper_id)

        if mapping:
            gsis_id = mapping["player_id"]
            name = mapping["name"]
            position = mapping["position"]
            team = mapping["team"]
        else:
            gsis_id = None
            name = sleeper_info.get("full_name", sleeper_id)
            position = sleeper_info.get("position")
            team = sleeper_info.get("team")

        # Treat Sleeper IDs as strings everywhere
        player_stats = (
            weekly_stats
            .filter(
                pl.col("sleeper_id").cast(pl.Utf8) == sleeper_id
            )
            .sort("week")
            .to_dicts()
        )

        player_snaps = (
            snap_counts
            .filter(
                pl.col("sleeper_id").cast(pl.Utf8) == sleeper_id
            )
            .sort("week")
            .to_dicts()
        )

        player_status = (
            weekly_status
            .filter(
                pl.col("sleeper_id").cast(pl.Utf8) == sleeper_id
            )
            .sort("week")
            .to_dicts()
        )

        player_contexts.append({
            "sleeper_id": sleeper_id,
            "gsis_id": gsis_id,
            "name": name,
            "position": position,
            "team": team,
            "entity_type": "player",
            "lineup_status": (
                "starter"
                if sleeper_id in starters
                else "bench"
            ),
            "weekly_stats": player_stats,
            "snap_counts": player_snaps,
            "weekly_status": player_status,
        })

    return player_contexts

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

    player_contexts = build_player_contexts(
        roster,
        sleeper_players,
        roster_mapping,
        weekly_stats,
        snap_counts,
        weekly_status,
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
        "player_contexts": player_contexts,
    }