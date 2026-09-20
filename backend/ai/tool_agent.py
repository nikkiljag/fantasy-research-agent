import json
import re

from foundry_local_sdk import (
    ChatSession,
    MessageItem,
    Request,
    RequestOptions,
    SearchOptions,
    TextItem,
    ToolCallItem,
    ToolChoice,
    ToolResultItem,
)

from ai.foundry_local import (
    get_model,
)

from services.player_tools import (
    search_players,
)


# ============================================================
# METRICS
# ============================================================

TREND_METRICS = {
    "carries_trend",
    "targets_trend",
    "opportunities_trend",
    "snap_pct_trend",
    "ppr_trend",
}


ALL_METRICS = [
    "games",

    "avg_carries",
    "avg_targets",
    "avg_opportunities",
    "avg_snap_pct",
    "avg_ppr",

    "carries_trend",
    "targets_trend",
    "opportunities_trend",
    "snap_pct_trend",
    "ppr_trend",
]


# ============================================================
# TOOL SCHEMA
# ============================================================

SEARCH_PLAYERS_SCHEMA = {
    "type": "object",
    "properties": {

        "position": {
            "type": "string",
            "enum": [
                "QB",
                "RB",
                "WR",
                "TE",
            ],
            "description": (
                "Fantasy football position to research."
            ),
        },

        "availability": {
            "type": "string",
            "enum": [
                "unrostered",
                "rostered",
                "all",
            ],
            "description": (
                "Ownership status. Available, waiver, "
                "free-agent, and unowned players mean "
                "unrostered."
            ),
        },

        "sort_by": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ALL_METRICS,
            },
            "minItems": 1,
            "maxItems": 3,
            "description": (
                "Metrics used to rank players in priority order. "
                "Trend metrics measure whether usage or scoring "
                "has been increasing or decreasing over completed "
                "NFL weeks."
            ),
        },

        "filters": {
            "type": "array",
            "description": (
                "Optional numerical conditions players "
                "must satisfy."
            ),
            "items": {
                "type": "object",
                "properties": {

                    "metric": {
                        "type": "string",
                        "enum": ALL_METRICS,
                    },

                    "operator": {
                        "type": "string",
                        "enum": [
                            "gt",
                            "gte",
                            "lt",
                            "lte",
                            "eq",
                        ],
                    },

                    "value": {
                        "type": "number",
                    },
                },

                "required": [
                    "metric",
                    "operator",
                    "value",
                ],
            },
        },

        "last_n_weeks": {
            "type": "integer",
            "minimum": 1,
            "maximum": 18,
            "description": (
                "Optional recent completed-week window."
            ),
        },

        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 20,
        },
    },

    "required": [
        "availability",
        "sort_by",
    ],
}


# ============================================================
# AGENT INSTRUCTIONS
# ============================================================

SYSTEM_PROMPT = """
You are a fantasy football research agent.

Your job is to investigate fantasy questions using
deterministic analytics backed by the user's actual
league and NFL statistics.

OWNERSHIP:

- available = unrostered
- waiver = unrostered
- waiver wire = unrostered
- free agent = unrostered
- unowned = unrostered
- rostered = rostered
- owned = rostered

BASIC METRICS:

- avg_carries = rushing attempts per game
- avg_targets = targets per game
- avg_opportunities = carries + targets per game
- avg_snap_pct = offensive snap percentage
- avg_ppr = PPR fantasy points per game

TREND METRICS:

- carries_trend = change in carries per week
- targets_trend = change in targets per week
- opportunities_trend = change in carries + targets per week
- snap_pct_trend = change in snap percentage points per week
- ppr_trend = change in fantasy scoring per week

CASUAL RESEARCH QUESTIONS:

If a user asks about concepts like:
- upside
- breakout potential
- emerging players
- increasing role
- players trending upward

consider whether recent usage trends are relevant.

For WR and TE upside, targets, target trend, snap share,
and snap-share trend can be useful.

For RB upside, opportunities, opportunity trend, snap share,
and snap-share trend can be useful.

Do not assume historical usage guarantees future performance.

IMPORTANT:

The analytics system may report that there are not yet enough
fully completed NFL weeks for reliable trend analysis.

If that happens:
- Do not pretend trend evidence exists.
- Use the fallback usage evidence returned by the tool.
- Clearly tell the user that trend history is not mature yet.
- Frame the result as current usage-based candidates rather
  than a reliable future projection.

RULES:

- Never guess ownership.
- Never invent statistics.
- Never invent injuries, matchups, depth-chart changes,
  news, projections, or schedule facts.
- Base conclusions only on tool-returned evidence.
"""


# ============================================================
# SEMANTIC GUARDRAILS
# ============================================================

def normalize_search_arguments(
    question,
    arguments,
):
    """
    Validate important meanings after Foundry proposes
    its tool arguments.
    """

    normalized = dict(
        arguments
    )

    question_lower = (
        question.lower()
    )


    # --------------------------------------------------------
    # OWNERSHIP
    # --------------------------------------------------------

    unrostered_phrases = [
        "available",
        "waiver",
        "free agent",
        "free-agent",
        "unrostered",
        "unowned",
        "not rostered",
    ]

    rostered_phrases = [
        "rostered players",
        "owned players",
    ]


    if any(
        phrase in question_lower
        for phrase in unrostered_phrases
    ):

        normalized[
            "availability"
        ] = "unrostered"

    elif any(
        phrase in question_lower
        for phrase in rostered_phrases
    ):

        normalized[
            "availability"
        ] = "rostered"


    # --------------------------------------------------------
    # DEFAULTS
    # --------------------------------------------------------

    normalized.setdefault(
        "availability",
        "all",
    )

    normalized.setdefault(
        "sort_by",
        [
            "avg_opportunities"
        ],
    )

    normalized.setdefault(
        "filters",
        [],
    )

    normalized.setdefault(
        "limit",
        10,
    )


    return normalized


# ============================================================
# FALLBACK LOGIC
# ============================================================

def question_has_explicit_week_window(
    question,
):
    """
    Determine whether the user explicitly requested a
    historical window such as 'last 3 weeks'.
    """

    return bool(
        re.search(
            r"\blast\s+\d+\s+weeks?\b",
            question.lower(),
        )
    )


def get_fallback_sort_metrics(
    position,
    original_sort,
):
    """
    Remove unavailable trend metrics and choose sensible
    non-trend evidence when necessary.
    """

    non_trend_metrics = [
        metric
        for metric in original_sort
        if metric not in TREND_METRICS
    ]


    if non_trend_metrics:

        return (
            non_trend_metrics[:3]
        )


    if position == "RB":

        return [
            "avg_opportunities",
            "avg_snap_pct",
            "avg_ppr",
        ]


    if position in {
        "WR",
        "TE",
    }:

        return [
            "avg_targets",
            "avg_snap_pct",
            "avg_ppr",
        ]


    if position == "QB":

        return [
            "avg_ppr",
        ]


    return [
        "avg_ppr",
    ]


def build_fallback_arguments(
    question,
    arguments,
):
    """
    Build a safe alternative query when trend analysis
    cannot yet be calculated.
    """

    fallback = dict(
        arguments
    )


    fallback["sort_by"] = (
        get_fallback_sort_metrics(
            fallback.get(
                "position"
            ),

            fallback.get(
                "sort_by",
                [],
            ),
        )
    )


    # Remove filters that depend on trend calculations.
    fallback["filters"] = [
        item
        for item in fallback.get(
            "filters",
            [],
        )
        if item.get(
            "metric"
        ) not in TREND_METRICS
    ]


    # If the user did NOT explicitly request a historical
    # window, allow ordinary averages to use the latest
    # available player data.
    if not question_has_explicit_week_window(
        question
    ):

        fallback.pop(
            "last_n_weeks",
            None,
        )


    return fallback


# ============================================================
# TOOL EXECUTION
# ============================================================

def run_player_search(
    arguments,
):
    """
    Execute the deterministic search_players tool.
    """

    return search_players(
        position=arguments.get(
            "position"
        ),

        availability=arguments.get(
            "availability",
            "all",
        ),

        sort_by=arguments.get(
            "sort_by",
            [
                "avg_opportunities"
            ],
        ),

        filters=arguments.get(
            "filters",
            [],
        ),

        last_n_weeks=arguments.get(
            "last_n_weeks"
        ),

        limit=arguments.get(
            "limit",
            10,
        ),
    )


def execute_tool(
    question,
    function_name,
    arguments,
):
    """
    Execute research.

    If trend evidence is unavailable because too few
    NFL weeks are complete, automatically fall back
    to valid current usage evidence.
    """

    if function_name != "search_players":

        raise ValueError(
            f"Unknown tool: {function_name}"
        )


    try:

        results = run_player_search(
            arguments
        )


        return {
            "status": "success",

            "analysis_note": (
                "The requested analytics were available."
            ),

            "used_arguments": arguments,

            "rows": (
                results.to_dicts()
            ),
        }


    except ValueError as error:

        error_message = str(
            error
        )


        trend_not_ready = (
            "Trend analysis requires"
            in error_message
            or
            "Trend analysis is not available"
            in error_message
        )


        if not trend_not_ready:
            raise


        fallback_arguments = (
            build_fallback_arguments(
                question,
                arguments,
            )
        )


        print(
            "\nTrend data is not mature yet."
        )

        print(
            "Falling back to current "
            "usage-based evidence."
        )

        print(
            f"Fallback arguments: "
            f"{fallback_arguments}"
        )


        results = run_player_search(
            fallback_arguments
        )


        return {
            "status": "fallback",

            "analysis_note": (
                f"{error_message} "
                "The system therefore used current "
                "usage and fantasy-production averages "
                "instead of trend metrics. "
                "This is not a true future projection."
            ),

            "requested_arguments": (
                arguments
            ),

            "used_arguments": (
                fallback_arguments
            ),

            "rows": (
                results.to_dicts()
            ),
        }


# ============================================================
# RESPONSE READER
# ============================================================

def read_response(response):

    text_parts = []
    tool_calls = []


    for item in response:

        if isinstance(
            item,
            ToolCallItem,
        ):

            tool_calls.append({
                "call_id": item.call_id,
                "name": item.name,
                "arguments": item.arguments,
            })


        elif isinstance(
            item,
            TextItem,
        ):

            text_parts.append(
                item.text
            )


        elif isinstance(
            item,
            MessageItem,
        ):

            for part in item.parts:

                if isinstance(
                    part,
                    TextItem,
                ):

                    text_parts.append(
                        part.text
                    )


    return (
        "".join(
            text_parts
        ).strip(),

        tool_calls,
    )


# ============================================================
# AGENT
# ============================================================

def run_tool_agent(
    question,
):

    model = get_model()

    tool_history = []


    with ChatSession(
        model
    ) as session:


        # ----------------------------------------------------
        # REGISTER RESEARCH TOOL
        # ----------------------------------------------------

        session.add_tool_definition(
            name="search_players",

            description=(
                "Search fantasy football players using "
                "actual league ownership and NFL statistics. "
                "Supports averages, numerical filters, recent "
                "week windows, and usage/scoring trends."
            ),

            json_schema=json.dumps(
                SEARCH_PLAYERS_SCHEMA
            ),
        )


        # ----------------------------------------------------
        # PLANNING TURN
        # ----------------------------------------------------

        session.set_options(
            RequestOptions(
                search=SearchOptions(
                    temperature=0.0,
                    max_output_tokens=500,
                ),

                tool_choice=(
                    ToolChoice.REQUIRED
                ),
            )
        )


        with Request() as request:

            request.add_item(
                MessageItem.system(
                    SYSTEM_PROMPT
                )
            )

            request.add_item(
                MessageItem.user(
                    question
                )
            )


            with session.process_request(
                request
            ) as response:

                (
                    first_text,
                    tool_calls,
                ) = read_response(
                    response
                )


        if not tool_calls:

            raise RuntimeError(
                "Foundry did not return a "
                "structured tool call."
            )


        # ----------------------------------------------------
        # EXECUTE RESEARCH
        # ----------------------------------------------------

        with Request() as follow_up:

            for tool_call in tool_calls:

                function_name = (
                    tool_call[
                        "name"
                    ]
                )


                proposed_arguments = (
                    json.loads(
                        tool_call[
                            "arguments"
                        ]
                    )
                )


                print(
                    "\nFoundry proposed arguments:"
                )

                print(
                    proposed_arguments
                )


                arguments = (
                    normalize_search_arguments(
                        question,
                        proposed_arguments,
                    )
                )


                print(
                    "\nValidated tool call:"
                )

                print(
                    function_name
                )

                print(
                    f"Arguments: {arguments}"
                )


                result = execute_tool(
                    question,
                    function_name,
                    arguments,
                )


                tool_history.append({
                    "tool": function_name,
                    "arguments": arguments,
                    "result": result,
                })


                follow_up.add_item(
                    ToolResultItem(
                        call_id=(
                            tool_call[
                                "call_id"
                            ]
                        ),

                        result=json.dumps(
                            result,
                            default=str,
                        ),
                    )
                )


            # ------------------------------------------------
            # FINAL EXPLANATION
            # ------------------------------------------------

            session.set_options(
                RequestOptions(
                    search=SearchOptions(
                        temperature=0.0,
                        max_output_tokens=900,
                    ),

                    tool_choice=(
                        ToolChoice.NONE
                    ),
                )
            )


            with session.process_request(
                follow_up
            ) as response:

                (
                    answer_text,
                    extra_tool_calls,
                ) = read_response(
                    response
                )


        return {
            "answer": answer_text,
            "tool_history": (
                tool_history
            ),
        }