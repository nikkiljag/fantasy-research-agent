import json

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
                "Optional fantasy football position."
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
                "enum": [
                    "games",
                    "avg_carries",
                    "avg_targets",
                    "avg_opportunities",
                    "avg_snap_pct",
                    "avg_ppr",
                ],
            },
            "minItems": 1,
            "maxItems": 3,
            "description": (
                "Metrics used to rank results in priority order."
            ),
        },

        "filters": {
            "type": "array",
            "description": (
                "Optional numerical conditions that players "
                "must satisfy."
            ),
            "items": {
                "type": "object",
                "properties": {

                    "metric": {
                        "type": "string",
                        "enum": [
                            "games",
                            "avg_carries",
                            "avg_targets",
                            "avg_opportunities",
                            "avg_snap_pct",
                            "avg_ppr",
                        ],
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
                        "description": (
                            "gt = greater than, "
                            "gte = at least, "
                            "lt = less than, "
                            "lte = at most, "
                            "eq = equal to."
                        ),
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
                "Restrict research to the most recent "
                "N NFL weeks available in the database."
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

Use search_players to answer questions about NFL players
using real fantasy league ownership and NFL statistics.

OWNERSHIP:

- available = unrostered
- waiver = unrostered
- free agent = unrostered
- unowned = unrostered
- owned = rostered
- rostered = rostered

METRICS:

- avg_carries = average rushing attempts per game
- avg_targets = average targets per game
- avg_opportunities = average carries + targets per game
- avg_snap_pct = average offensive snap percentage
- avg_ppr = average PPR fantasy points per game
- games = number of games in the selected window

FILTER LANGUAGE:

- "under 10 PPR" means:
  metric=avg_ppr, operator=lt, value=10

- "at least 6 targets" means:
  metric=avg_targets, operator=gte, value=6

- "over 50 percent snap share" means:
  metric=avg_snap_pct, operator=gt, value=50

TIME WINDOWS:

If the user says:
- "last 2 weeks" -> last_n_weeks=2
- "last 3 weeks" -> last_n_weeks=3

RULES:

- Use only tool-returned evidence.
- Never invent statistics.
- Never guess player availability.
- Do not invent injuries, news, matchups, depth-chart changes,
  or other information not returned by a tool.
- Choose ranking metrics that match what the user actually asks.
"""


# ============================================================
# ARGUMENT GUARDRAILS
# ============================================================

def normalize_search_arguments(
    question,
    arguments,
):
    """
    Apply deterministic semantic guardrails after the
    model proposes tool arguments.
    """

    normalized = dict(
        arguments
    )

    question_lower = (
        question.lower()
    )


    # --------------------------------------------------------
    # OWNERSHIP LANGUAGE
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
# TOOL EXECUTION
# ============================================================

def execute_tool(
    function_name,
    arguments,
):
    """
    Execute an approved deterministic research tool.
    """

    if function_name == "search_players":

        results = search_players(
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

        return {
            "rows": (
                results.to_dicts()
            )
        }


    raise ValueError(
        f"Unknown tool: {function_name}"
    )


# ============================================================
# RESPONSE READER
# ============================================================

def read_response(response):
    """
    Extract text and structured tool calls.
    """

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

def run_tool_agent(question):

    model = get_model()

    tool_history = []


    with ChatSession(
        model
    ) as session:


        # ----------------------------------------------------
        # REGISTER GENERIC RESEARCH TOOL
        # ----------------------------------------------------

        session.add_tool_definition(
            name="search_players",

            description=(
                "Search NFL fantasy players using real league "
                "ownership and NFL statistics. Supports position, "
                "availability, multiple ranking metrics, numerical "
                "filters, and recent-week windows."
            ),

            json_schema=json.dumps(
                SEARCH_PLAYERS_SCHEMA
            ),
        )


        # ----------------------------------------------------
        # RESEARCH / TOOL PLANNING
        # ----------------------------------------------------

        session.set_options(
            RequestOptions(
                search=SearchOptions(
                    temperature=0.0,
                    max_output_tokens=450,
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
                    tool_call["name"]
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
            # FINAL ANSWER
            # ------------------------------------------------

            session.set_options(
                RequestOptions(
                    search=SearchOptions(
                        temperature=0.0,
                        max_output_tokens=700,
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