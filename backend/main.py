from ai.foundry_local import (
    run_local_chat,
)


print(
    "\n=============================="
)

print(
    "FOUNDRY LOCAL TEST"
)

print(
    "=============================="
)


messages = [
    {
        "role": "system",
        "content": (
            "You are the AI reasoning component of a "
            "fantasy football research application. "
            "Answer clearly and concisely."
        ),
    },
    {
        "role": "user",
        "content": (
            "In one sentence, explain why target volume "
            "can matter for evaluating a fantasy football "
            "wide receiver."
        ),
    },
]


response = run_local_chat(
    messages
)


print(
    "\nLocal AI response:\n"
)

print(
    response
)