def safe_sum(rows, field):
    """
    Sum a numeric field across weekly rows.

    Returns None when there are no statistical rows,
    so missing data is not confused with a real zero.
    """

    if not rows:
        return None

    return sum(
        row.get(field) or 0
        for row in rows
    )


def safe_average(values):
    """
    Average a list of numeric values.
    """

    clean_values = [
        value
        for value in values
        if value is not None
    ]

    if not clean_values:
        return None

    return sum(clean_values) / len(clean_values)


def get_latest_record(rows):
    """
    Return the record from the highest available week.
    """

    if not rows:
        return None

    return max(
        rows,
        key=lambda row: row.get("week", 0)
    )


def summarize_player(player):
    """
    Convert raw player context into a clean,
    position-aware season summary.
    """

    stats = player["weekly_stats"]
    snaps = player["snap_counts"]
    statuses = player["weekly_status"]

    latest_game = get_latest_record(stats)
    latest_snap = get_latest_record(snaps)
    latest_status = get_latest_record(statuses)

    fantasy_points = [
        row.get("fantasy_points_ppr")
        for row in stats
        if row.get("fantasy_points_ppr") is not None
    ]

    summary = {
        "name": player["name"],
        "position": player["position"],
        "team": player["team"],
        "lineup_status": player["lineup_status"],
        "entity_type": player["entity_type"],

        "games_with_stats": len(stats),

        "latest_game_week": (
            latest_game.get("week")
            if latest_game
            else None
        ),

        "latest_status": (
            latest_status.get("status")
            if latest_status
            else None
        ),

        "latest_status_week": (
            latest_status.get("week")
            if latest_status
            else None
        ),

        "latest_offense_snap_pct": (
            latest_snap.get("offense_pct")
            if latest_snap
            else None
        ),

        "latest_snap_week": (
            latest_snap.get("week")
            if latest_snap
            else None
        ),

        "fantasy": {
            "total_ppr_points": (
                round(sum(fantasy_points), 2)
                if fantasy_points
                else None
            ),

            "average_ppr_points": (
                round(
                    safe_average(fantasy_points),
                    2
                )
                if fantasy_points
                else None
            ),

            "weekly_ppr_points": fantasy_points,
        },
    }

    position = player["position"]

    # ==================================================
    # QUARTERBACKS
    # ==================================================

    if position == "QB":

        summary["passing"] = {
            "completions": safe_sum(
                stats,
                "completions"
            ),

            "attempts": safe_sum(
                stats,
                "attempts"
            ),

            "yards": safe_sum(
                stats,
                "passing_yards"
            ),

            "touchdowns": safe_sum(
                stats,
                "passing_tds"
            ),

            "interceptions": safe_sum(
                stats,
                "passing_interceptions"
            ),
        }

        summary["rushing"] = {
            "carries": safe_sum(
                stats,
                "carries"
            ),

            "yards": safe_sum(
                stats,
                "rushing_yards"
            ),

            "touchdowns": safe_sum(
                stats,
                "rushing_tds"
            ),
        }

    # ==================================================
    # RUNNING BACKS
    # ==================================================

    elif position == "RB":

        summary["rushing"] = {
            "carries": safe_sum(
                stats,
                "carries"
            ),

            "yards": safe_sum(
                stats,
                "rushing_yards"
            ),

            "touchdowns": safe_sum(
                stats,
                "rushing_tds"
            ),
        }

        summary["receiving"] = {
            "targets": safe_sum(
                stats,
                "targets"
            ),

            "receptions": safe_sum(
                stats,
                "receptions"
            ),

            "yards": safe_sum(
                stats,
                "receiving_yards"
            ),

            "touchdowns": safe_sum(
                stats,
                "receiving_tds"
            ),
        }

    # ==================================================
    # WR / TE
    # ==================================================

    elif position in ("WR", "TE"):

        summary["receiving"] = {
            "targets": safe_sum(
                stats,
                "targets"
            ),

            "receptions": safe_sum(
                stats,
                "receptions"
            ),

            "yards": safe_sum(
                stats,
                "receiving_yards"
            ),

            "touchdowns": safe_sum(
                stats,
                "receiving_tds"
            ),

            "air_yards": safe_sum(
                stats,
                "receiving_air_yards"
            ),
        }

        summary["rushing"] = {
            "carries": safe_sum(
                stats,
                "carries"
            ),

            "yards": safe_sum(
                stats,
                "rushing_yards"
            ),
        }

    # ==================================================
    # KICKERS
    # ==================================================

    elif position in ("K", "PK"):

        summary["kicking"] = {
            "fantasy_points": (
                round(sum(fantasy_points), 2)
                if fantasy_points
                else None
            )
        }

    # ==================================================
    # TEAM DEFENSES
    # ==================================================

    elif position == "DEF":

        summary["defense"] = {
            "status": "team-level stats not integrated yet"
        }

    # ==================================================
    # CHART / TREND DATA
    # ==================================================

    summary["series"] = {
        "fantasy_points_ppr": [
            {
                "week": row.get("week"),
                "value": row.get("fantasy_points_ppr"),
            }
            for row in stats
            if row.get("fantasy_points_ppr") is not None
        ],

        "snap_pct": [
            {
                "week": row.get("week"),
                "value": row.get("offense_pct"),
            }
            for row in snaps
            if row.get("offense_pct") is not None
        ],
    }

    if position == "RB":

        summary["series"]["carries"] = [
            {
                "week": row.get("week"),
                "value": row.get("carries"),
            }
            for row in stats
            if row.get("carries") is not None
        ]

        summary["series"]["targets"] = [
            {
                "week": row.get("week"),
                "value": row.get("targets"),
            }
            for row in stats
            if row.get("targets") is not None
        ]

    elif position in ("WR", "TE"):

        summary["series"]["targets"] = [
            {
                "week": row.get("week"),
                "value": row.get("targets"),
            }
            for row in stats
            if row.get("targets") is not None
        ]

        summary["series"]["air_yards"] = [
            {
                "week": row.get("week"),
                "value": row.get("receiving_air_yards"),
            }
            for row in stats
            if row.get("receiving_air_yards") is not None
        ]

    elif position == "QB":

        summary["series"]["pass_attempts"] = [
            {
                "week": row.get("week"),
                "value": row.get("attempts"),
            }
            for row in stats
            if row.get("attempts") is not None
        ]

    return summary


def summarize_team(player_contexts):
    """
    Build summaries for every player on the roster.
    """

    return [
        summarize_player(player)
        for player in player_contexts
    ]