from services.research import (
    get_database_schema,
    run_research_query,
)


print("\n==============================")
print("RESEARCH DATABASE")
print("==============================")


schema = get_database_schema()

print("\nAvailable tables:")

for table_name in schema:
    print(
        f"- {table_name}: "
        f"{len(schema[table_name])} columns"
    )


print("\n==============================")
print("RESEARCH QUERY TEST")
print("==============================")


query = """
SELECT
    name,
    position,
    team,

    COUNT(*) AS games,

    ROUND(
        AVG(
            COALESCE(targets, 0)
            +
            COALESCE(carries, 0)
        ),
        2
    ) AS avg_opportunities,

    ROUND(
        AVG(offense_pct) * 100,
        1
    ) AS avg_snap_pct,

    ROUND(
        AVG(fantasy_points_ppr),
        2
    ) AS avg_ppr

FROM player_week

WHERE position IN (
    'RB',
    'WR',
    'TE'
)

GROUP BY
    sleeper_id,
    name,
    position,
    team

ORDER BY
    avg_opportunities DESC

LIMIT 10
"""


results = run_research_query(
    query
)

print(
    "\nHighest-usage fantasy players:\n"
)

print(
    results
)