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
                "Player ownership status. "
                "IMPORTANT: available players, waiver players, "
                "free agents, and unrostered players all mean "
                "'unrostered'."
            ),
        },

        "sort_by": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
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
                "Metrics used to rank players in priority order. "
                "The first metric is primary, followed by "
                "secondary tie-breaking metrics."
            ),
        },

        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 20,
            "description": (
                "Maximum number of players returned."
            ),
        },
    },

    "required": [
        "position",
        "availability",
        "sort_by",
    ],
}


# ============================================================
# AGENT INSTRUCTIONS
# ============================================================

SYSTEM_PROMPT = """
You are a fantasy football research agent.

You have access to deterministic analytics backed by
the user's actual fantasy league and NFL statistics.

Use search_players for player research.

OWNERSHIP TERMINOLOGY:

- "available" means unrostered
- "waiver" or "waiver wire" means unrostered
- "free agent" means unrostered
- "unowned" means unrostered
- "unrostered" means unrostered
- "rostered" or "owned" means rostered

Never call rostered players available.

DATA RULES:

- Do not guess ownership.
- Do not invent statistics.
- Do not invent injuries, news, matchups, or depth-chart changes.
- Base conclusions only on tool evidence.
- Describe players relative to the requested metrics rather than
  claiming they are universally the best.

METRIC GUIDANCE:

RB:
- avg_carries = rushing workload
- avg_targets = receiving involvement
- avg_opportunities = carries + targets
- avg_snap_pct = percentage of offensive snaps played
- avg_ppr = fantasy production

WR / TE:
- avg_targets is generally highly relevant
- avg_snap_pct gives participation context
- avg_ppr measures realized fantasy production

QB:
- Current generic metrics are limited for quarterback analysis.

SORTING:

sort_by is ordered by priority.

Example:

["avg_targets", "avg_snap_pct"]

means primarily rank by targets, then by snap share.
"""


# ============================================================
# ARGUMENT GUARDRAILS
# ============================================================

def normalize_search_arguments(
    question,
    arguments,
):
    """
    Validate and correct important semantic constraints.

    The LLM proposes arguments, but deterministic Python
    has final authority over meanings such as "available".
    """

    normalized = dict(
        arguments
    )

    question_lower = (
        question
        .lower()
    )


    # --------------------------------------------------------
    # AVAILABILITY
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
    Execute an approved fantasy research tool.
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

            limit=arguments.get(
                "limit",
                10,
            ),
        )

        return {
            "rows": results.to_dicts()
        }

    raise ValueError(
        f"Unknown tool: {function_name}"
    )


# ============================================================
# RESPONSE READER
# ============================================================

def read_response(response):
    """
    Extract text and structured tool calls from
    a Foundry Local response.
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
    """
    Run a generic fantasy-player research cycle.
    """

    model = get_model()

    tool_history = []

    with ChatSession(
        model
    ) as session:

        # ----------------------------------------------------
        # REGISTER TOOL
        # ----------------------------------------------------

        session.add_tool_definition(
            name="search_players",

            description=(
                "Search fantasy football players using "
                "NFL statistics and actual league ownership. "
                "Available, waiver, free-agent, and unrostered "
                "player searches must use availability='unrostered'."
            ),

            json_schema=json.dumps(
                SEARCH_PLAYERS_SCHEMA
            ),
        )


        # ----------------------------------------------------
        # ASK FOUNDRY TO PLAN TOOL CALL
        # ----------------------------------------------------

        session.set_options(
            RequestOptions(
                search=SearchOptions(
                    temperature=0.0,
                    max_output_tokens=350,
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
        # EXECUTE TOOL
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


                # Python validates/corrects semantic constraints.
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
                    f"{function_name}"
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
            # FINAL NATURAL-LANGUAGE ANSWER
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