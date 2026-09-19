import nflreadpy as nfl
import polars as pl


# ============================================================
# PLAYER ID MAPPING
# ============================================================

def load_player_id_map():
    """
    Load nflverse cross-platform player ID mappings.
    """
    return nfl.load_ff_playerids()


def build_roster_mapping(sleeper_player_ids):
    """
    Convert Sleeper player IDs into nflverse / GSIS player IDs.

    Team defenses such as PIT are ignored because they are
    team-level entities rather than individual players.
    """

    numeric_ids = [
        int(player_id)
        for player_id in sleeper_player_ids
        if player_id.isdigit()
    ]

    player_ids = load_player_id_map()

    return (
        player_ids
        .filter(
            pl.col("sleeper_id").is_in(numeric_ids)
        )
        .select([
            pl.col("gsis_id").alias("player_id"),
            "name",
            "position",
            "team",
            pl.col("sleeper_id")
            .cast(pl.Utf8)
            .alias("sleeper_id"),
        ])
    )


# ============================================================
# WEEKLY PLAYER STATS
# ============================================================

def load_weekly_stats(season=2026):
    """
    Load nflverse weekly player statistics.
    """

    return nfl.load_player_stats(
        seasons=season,
        summary_level="week",
    )


def get_roster_weekly_stats(
    roster_mapping,
    season=2026,
):
    """
    Join fantasy roster players to weekly NFL statistics.
    """

    stats = load_weekly_stats(season)

    roster_info = roster_mapping.select([
        "player_id",
        "name",
        "position",
        "team",
        "sleeper_id",
    ])

    return (
        stats
        .join(
            roster_info,
            on="player_id",
            how="inner",
        )
    )


def get_players_missing_stats(
    roster_mapping,
    roster_stats,
):
    """
    Identify mapped fantasy players who currently
    have no weekly nflverse statistical rows.
    """

    players_with_stats = set(
        roster_stats
        .select("sleeper_id")
        .unique()
        .to_series()
        .to_list()
    )

    mapped_ids = set(
        roster_mapping
        .select("sleeper_id")
        .to_series()
        .to_list()
    )

    missing_ids = (
        mapped_ids - players_with_stats
    )

    if not missing_ids:
        return pl.DataFrame()

    return (
        roster_mapping
        .filter(
            pl.col("sleeper_id").is_in(
                list(missing_ids)
            )
        )
        .select([
            "name",
            "position",
            "team",
            "sleeper_id",
            "player_id",
        ])
    )


# ============================================================
# SNAP COUNTS
# ============================================================

def load_snap_counts(season=2026):
    """
    Load NFL snap-count data.
    """

    return nfl.load_snap_counts(
        seasons=season
    )


def build_gsis_to_pfr_mapping():
    """
    Build a bridge between GSIS IDs and
    Pro Football Reference player IDs.
    """

    players = nfl.load_players()

    return (
        players
        .select([
            pl.col("gsis_id")
            .alias("player_id"),

            pl.col("pfr_id")
            .alias("pfr_player_id"),
        ])
        .drop_nulls()
    )


def get_roster_snap_counts(
    roster_mapping,
    season=2026,
):
    """
    Retrieve snap-count data for players
    on the fantasy roster.
    """

    snap_counts = load_snap_counts(season)

    id_bridge = build_gsis_to_pfr_mapping()

    snaps_with_gsis = (
        snap_counts
        .join(
            id_bridge,
            on="pfr_player_id",
            how="inner",
        )
    )

    roster_info = roster_mapping.select([
        "player_id",
        "name",
        "position",
        "sleeper_id",
    ])

    return (
        snaps_with_gsis
        .join(
            roster_info,
            on="player_id",
            how="inner",
        )
    )


# ============================================================
# WEEKLY NFL ROSTER STATUS
# ============================================================

def load_weekly_rosters(season=2026):
    """
    Load week-by-week NFL roster information.
    """

    return nfl.load_rosters_weekly(
        seasons=season
    )


def get_roster_weekly_status(
    roster_mapping,
    season=2026,
):
    """
    Retrieve weekly NFL roster status for players
    on the fantasy roster.
    """

    weekly_rosters = (
        load_weekly_rosters(season)
    )

    roster_info = roster_mapping.select([
        pl.col("player_id")
        .alias("gsis_id"),

        "name",
        "position",
        "sleeper_id",
    ])

    return (
        weekly_rosters
        .join(
            roster_info,
            on="gsis_id",
            how="inner",
        )
    )