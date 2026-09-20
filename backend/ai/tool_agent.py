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
    find_available_players,
)


AVAILABLE_PLAYERS_SCHEMA = {
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
                "Fantasy football position to search."
            ),
        },

        "sort_by": {
            "type": "string",
            "enum": [
                "avg_carries",
                "avg_targets",
                "avg_opportunities",
                "avg_snap_pct",
                "avg_ppr",
            ],
            "description": (
                "Metric used to rank players. "
                "For running backs emphasizing carries "
                "and snap share, avg_carries is useful "
                "because the returned table also contains "
                "avg_snap_pct."
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
    ],
}


SYSTEM_PROMPT = """
You are a fantasy football research agent.

You have access to deterministic analytical tools backed
by the user's real fantasy league and NFL statistics.

RULES:

- Use the provided research tool to answer the question.
- Do not guess which players are available.
- Do not invent statistics.
- Do not invent injuries, news, matchups, or league data.
- Base your conclusions only on information returned
  by the tool.
- Explain the most relevant numbers clearly.
- For running backs, carries, targets, opportunities,
  snap share, and fantasy production can all be useful.
"""


def execute_tool(
    function_name,
    arguments,
):
    """
    Execute an approved fantasy research tool.
    """

    if function_name == "find_available_players":

        results = find_available_players(
            position=arguments["position"],

            sort_by=arguments.get(
                "sort_by",
                "avg_opportunities",
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


def read_response(response):
    """
    Extract normal text and structured tool calls
    from a Foundry Local response.
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
        "".join(text_parts).strip(),
        tool_calls,
    )


def run_tool_agent(question):
    """
    Run one deterministic fantasy research cycle.

    Step 1:
        Force Foundry to make a structured tool call.

    Step 2:
        Execute the Python analytics tool.

    Step 3:
        Disable further tool calls and ask Foundry
        to explain the returned evidence.
    """

    model = get_model()

    tool_history = []

    with ChatSession(
        model
    ) as session:

        # ------------------------------------------
        # REGISTER TOOL
        # ------------------------------------------

        session.add_tool_definition(
            name="find_available_players",

            description=(
                "Find players who are currently "
                "unrostered in the user's fantasy "
                "football league and return their "
                "NFL usage and fantasy statistics."
            ),

            json_schema=json.dumps(
                AVAILABLE_PLAYERS_SCHEMA
            ),
        )


        # ------------------------------------------
        # FORCE STRUCTURED TOOL CALL
        # ------------------------------------------

        session.set_options(
            RequestOptions(
                search=SearchOptions(
                    temperature=0.0,
                    max_output_tokens=300,
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
                "Foundry did not return a structured "
                "tool call even though tool calling "
                "was required."
            )


        # ------------------------------------------
        # EXECUTE TOOL CALLS
        # ------------------------------------------

        with Request() as follow_up:

            for tool_call in tool_calls:

                function_name = (
                    tool_call["name"]
                )

                arguments = json.loads(
                    tool_call["arguments"]
                )

                print(
                    "\nFoundry requested tool: "
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


            # --------------------------------------
            # TOOL IS DONE
            #
            # Force the next turn to be normal text
            # instead of another function call.
            # --------------------------------------

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


        if extra_tool_calls:

            raise RuntimeError(
                "Foundry attempted another tool call "
                "after tool calling was disabled."
            )


        return {
            "answer": answer_text,
            "tool_history": tool_history,
        }