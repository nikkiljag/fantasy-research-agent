from foundry_local_sdk import (
    ChatSession,
    Configuration,
    FoundryLocalManager,
    MessageItem,
    Request,
    RequestOptions,
    SearchOptions,
    TextItem,
)


MODEL_ALIAS = "qwen2.5-coder-7b"

_initialized = False
_model = None


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


def get_model():
    """
    Retrieve, download, and load the configured model.
    """

    global _model

    if _model is not None:
        return _model

    manager = initialize_foundry()

    _model = manager.catalog.get_model(
        MODEL_ALIAS
    )

    if _model is None:
        raise ValueError(
            f"Foundry model not found: {MODEL_ALIAS}"
        )

    print(
        f"\nPreparing local model: "
        f"{_model.id}"
    )

    _model.download(
        lambda progress: print(
            f"\rModel download: "
            f"{progress:.1f}%",
            end="",
            flush=True,
        )
    )

    print()

    if not _model.is_loaded:

        print(
            "\nLoading model..."
        )

        _model.load()

    return _model


def extract_response_text(response):
    """
    Extract normal assistant text from a typed
    Foundry Local response.
    """

    text_parts = []

    for item in response:

        if isinstance(
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

    return "".join(
        text_parts
    ).strip()


def complete_chat(messages):
    """
    Compatibility helper for our older research-agent
    code, now using the Foundry Local v2 Session API.
    """

    model = get_model()

    with ChatSession(
        model
    ) as session:

        session.set_options(
            RequestOptions(
                search=SearchOptions(
                    temperature=0.0,
                    max_output_tokens=512,
                )
            )
        )

        with Request() as request:

            for message in messages:

                role = message["role"]
                content = message["content"]

                if role == "system":

                    request.add_item(
                        MessageItem.system(
                            content
                        )
                    )

                elif role == "user":

                    request.add_item(
                        MessageItem.user(
                            content
                        )
                    )

                elif role == "assistant":

                    request.add_item(
                        MessageItem.assistant(
                            content
                        )
                    )

                else:

                    raise ValueError(
                        f"Unsupported message role: {role}"
                    )

            with session.process_request(
                request
            ) as response:

                return extract_response_text(
                    response
                )


def stop_model():
    """
    Unload the model when the application exits.
    """

    global _model

    if _model is not None:

        if _model.is_loaded:

            _model.unload()

            print(
                "\nModel unloaded."
            )

    _model = None