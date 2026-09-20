import nflreadpy as nfl

from database import (
    get_connection,
    list_tables,
    save_dataframe,
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


SEASON = 2026


def refresh_data(
    username,
    season=SEASON,
):
    """
    Refresh all data used by the fantasy
    research application.
    """

    print("\n==============================")
    print("REFRESHING FANTASY DATA")
    print("==============================")


    # --------------------------------------------------------
    # USER + LEAGUE
    # --------------------------------------------------------

    print("\nLoading Sleeper team...")

    team = get_team_context(
        username,
        season=season,
    )

    league_id = (
        team["league"]["league_id"]
    )

    print(
        f"League: {team['league']['name']}"
    )


    # --------------------------------------------------------
    # LEAGUE OWNERSHIP
    # --------------------------------------------------------

    print("\nLoading league ownership...")

    league_ownership = (
        get_league_ownership(
            league_id
        )
    )

    print(
        f"Rostered entities: "
        f"{league_ownership.height}"
    )


    # --------------------------------------------------------
    # NFL DATA
    # --------------------------------------------------------

    print("\nLoading player identities...")

    player_identity = (
        get_player_identity_table()
    )


    print("\nLoading weekly stats...")

    weekly_stats = (
        get_all_weekly_stats(
            season=season
        )
    )


    print("\nLoading snap counts...")

    snap_counts = (
        get_all_snap_counts(
            season=season
        )
    )


    print("\nLoading weekly roster status...")

    weekly_status = (
        get_all_weekly_status(
            season=season
        )
    )


    print("\nLoading NFL schedule...")

    schedule = nfl.load_schedules(
        seasons=season
    )


    # --------------------------------------------------------
    # UNIFIED ANALYTICS TABLE
    # --------------------------------------------------------

    print(
        "\nBuilding player-week table..."
    )

    player_week = (
        build_player_week_table(
            weekly_stats,
            snap_counts,
            weekly_status,
        )
    )


    # --------------------------------------------------------
    # SAVE DATABASE
    # --------------------------------------------------------

    print("\nSaving DuckDB tables...")

    save_team_data(
        team
    )

    save_league_ownership(
        league_ownership
    )

    save_league_nfl_data(
        player_identity,
        weekly_stats,
        snap_counts,
        weekly_status,
        player_week,
    )


    connection = get_connection()

    try:

        save_dataframe(
            connection,
            "nfl_schedule",
            schedule,
        )

    finally:

        connection.close()


    # --------------------------------------------------------
    # DONE
    # --------------------------------------------------------

    print("\n==============================")
    print("REFRESH COMPLETE")
    print("==============================")

    print(
        "\nTables:",
        list_tables(),
    )

    print(
        f"\nPlayer-week rows: "
        f"{player_week.height}"
    )


if __name__ == "__main__":

    sleeper_username = input(
        "Enter your Sleeper username: "
    )

    refresh_data(
        sleeper_username
    )