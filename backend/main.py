from ai.foundry_local import (
    stop_model,
)

from ai.research_agent import (
    research,
)


print("\n==============================")
print("FANTASY RESEARCH AGENT")
print("==============================")


question = input(
    "\nAsk a fantasy football question: "
)


try:

    result = research(
        question
    )

    print(
        "\n=============================="
    )

    print(
        "GENERATED SQL"
    )

    print(
        "==============================\n"
    )

    print(
        result["sql"]
    )


    print(
        "\n=============================="
    )

    print(
        "DATABASE RESULTS"
    )

    print(
        "==============================\n"
    )

    print(
        result["results"]
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


    print(
        "\n=============================="
    )

    print(
        "VISUALIZATION SPEC"
    )

    print(
        "==============================\n"
    )

    print(
        result["visualization"]
    )


except Exception as error:

    print(
        f"\nResearch failed: {error}"
    )


finally:

    stop_model()