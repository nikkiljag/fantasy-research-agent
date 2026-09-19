def build_visualization_spec(results):
    """
    Inspect research results and produce a simple,
    frontend-friendly visualization specification.

    The underlying values always come directly
    from the database results.
    """

    if results.is_empty():
        return None

    columns = results.columns

    label_candidates = [
        "name",
        "player",
        "team",
        "position",
        "week",
    ]

    label_column = None

    for candidate in label_candidates:
        if candidate in columns:
            label_column = candidate
            break

    if label_column is None:
        return None

    numeric_columns = []

    for column_name, dtype in results.schema.items():

        dtype_string = str(dtype)

        if (
            "Int" in dtype_string
            or "Float" in dtype_string
            or "Decimal" in dtype_string
        ):
            numeric_columns.append(
                column_name
            )

    # Remove fields that usually make poor chart metrics
    ignored_columns = {
        "week",
        "roster_id",
        "sleeper_id",
    }

    numeric_columns = [
        column
        for column in numeric_columns
        if column not in ignored_columns
    ]

    if not numeric_columns:
        return None

    # Keep charts readable
    selected_metrics = (
        numeric_columns[:3]
    )

    rows = (
        results
        .head(10)
        .to_dicts()
    )

    return {
        "type": "bar",
        "label_column": label_column,
        "metrics": selected_metrics,
        "rows": rows,
    }