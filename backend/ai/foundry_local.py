from foundry_local_sdk import (
    Configuration,
    FoundryLocalManager,
)


MODEL_ALIAS = "qwen2.5-0.5b"

_initialized = False


def initialize_foundry():
    """
    Initialize Foundry Local once for this Python process.
    """

    global _initialized

    if not _initialized:

        config = Configuration(
            app_name="fantasy-research-agent"
        )

        FoundryLocalManager.initialize(
            config
        )

        _initialized = True

    return FoundryLocalManager.instance


def get_model():
    """
    Get the configured local model from
    the Foundry Local catalog.
    """

    manager = initialize_foundry()

    return manager.catalog.get_model(
        MODEL_ALIAS
    )


def run_local_chat(messages):
    """
    Download/load the local model, send a chat request,
    return its response, and unload the model afterward.

    This is intentionally simple for our first test.
    """

    model = get_model()

    print(
        f"\nPreparing local model: "
        f"{MODEL_ALIAS}"
    )

    model.download(
        lambda progress: print(
            f"\rModel download: "
            f"{progress:.1f}%",
            end="",
            flush=True,
        )
    )

    print()

    print(
        "Loading model..."
    )

    model.load()

    try:

        client = model.get_chat_client()

        response = client.complete_chat(
            messages
        )

        return (
            response
            .choices[0]
            .message
            .content
        )

    finally:

        model.unload()

        print(
            "\nModel unloaded."
        )