import nflreadpy as nfl
import polars as pl


def load_player_id_map():
    """
    Load nflverse's cross-platform player ID mapping table.
    """
    return nfl.load_ff_playerids()


def build_roster_mapping(sleeper_player_ids):
    """
    Convert Sleeper player IDs into nflverse / GSIS player IDs.
    Team defenses like PIT should be excluded before calling this.
    """

    numeric_ids = [
        int(player_id)
        for player_id in sleeper_player_ids
        if player_id.isdigit()
    ]

    player_ids = load_player_id_map()

    return (
        player_ids
        .filter(pl.col("sleeper_id").is_in(numeric_ids))
        .select([
            pl.col("gsis_id").alias("player_id"),
            "name",
            "position",
            "team",
            "sleeper_id",
        ])
    )


def load_weekly_stats(season=2026):
    """
    Load nflverse weekly player statistics for a season.
    """
    return nfl.load_player_stats(
        seasons=season,
        summary_level="week"
    )


def get_roster_weekly_stats(roster_mapping, season=2026):
    """
    Join a mapped fantasy roster to nflverse weekly statistics.
    """

    stats = load_weekly_stats(season)

    return stats.join(
        roster_mapping,
        on="player_id",
        how="inner"
    )


def get_players_missing_stats(roster_mapping, roster_stats):
    """
    Identify mapped fantasy players who currently have
    no weekly nflverse stat rows.
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

    missing_ids = mapped_ids - players_with_stats

    if not missing_ids:
        return pl.DataFrame()

    return (
        roster_mapping
        .filter(pl.col("sleeper_id").is_in(list(missing_ids)))
        .select([
            "name",
            "position",
            "team",
            "sleeper_id",
            "player_id",
        ])
    )