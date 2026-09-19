# Data Sources

## Sleeper API

Purpose:

* identify users
* retrieve leagues
* retrieve league rosters
* retrieve player metadata

Current working endpoints:

* User lookup by username
* User leagues by season
* League rosters
* NFL player database

## Sleeper Player Cache

The full Sleeper NFL player database is cached locally at:

`data/cache/sleeper_players.json`

The cache is ignored by Git and should not be committed.

Player IDs from Sleeper rosters can now be translated into:

* player name
* position
* NFL team

Team defenses such as `PIT` are handled separately.

## Current Test League

League: Outside huzz
Season: 2026
Teams: 14

The backend can successfully identify the user's roster inside the league.
