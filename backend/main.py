from ai.foundry_local import (
    stop_model,
)

from ai.tool_agent import (
    run_tool_agent,
)


print("\n==============================")
print("FANTASY TOOL AGENT")
print("==============================")


question = input(
    "\nAsk a fantasy football question: "
)


try:

    result = run_tool_agent(
        question
    )


    print(
        "\n=============================="
    )

    print(
        "TOOL ACTIVITY"
    )

    print(
        "=============================="
    )


    for tool_call in result["tool_history"]:

        print(
            f"\nTool: "
            f"{tool_call['tool']}"
        )

        print(
            f"Arguments: "
            f"{tool_call['arguments']}"
        )


    print(
        "\n=============================="
    )

    print(
        "AI ANSWER"
    )

    print(
        "==============================\n"
    )

    print(
        result["answer"]
    )


except Exception as error:

    print(
        f"\nAgent failed: {error}"
    )


finally:

    stop_model()