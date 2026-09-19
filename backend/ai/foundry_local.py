from foundry_local_sdk import (
    Configuration,
    FoundryLocalManager,
)


MODEL_ALIAS = "qwen2.5-0.5b"

_initialized = False
_model = None
_client = None


def initialize_foundry():
    """
    Initialize Foundry Local once for this process.
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


def start_model():
    """
    Download and load the configured model once.
    """

    global _model
    global _client

    if _client is not None:
        return _client

    manager = initialize_foundry()

    _model = manager.catalog.get_model(
        MODEL_ALIAS
    )

    print(
        f"\nPreparing local model: {MODEL_ALIAS}"
    )

    _model.download(
        lambda progress: print(
            f"\rModel download: {progress:.1f}%",
            end="",
            flush=True,
        )
    )

    print("\nLoading model...")

    _model.load()

    _client = _model.get_chat_client()

    return _client


def complete_chat(messages):
    """
    Send messages to the currently loaded local model.
    """

    client = start_model()

    response = client.complete_chat(
        messages
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


def stop_model():
    """
    Unload the local model.
    """

    global _model
    global _client

    if _model is not None:

        _model.unload()

        print("\nModel unloaded.")

    _model = None
    _client = None