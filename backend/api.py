import os

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
)

from fastapi.security import APIKeyHeader

from pydantic import (
    BaseModel,
    Field,
)

from services.player_tools import (
    search_players,
)


app = FastAPI(
    title="Fantasy Research API",
    description=(
        "Deterministic fantasy football analytics "
        "for the Fantasy Research Agent."
    ),
    version="0.2.0",
)


API_KEY = os.getenv("FANTASY_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "FANTASY_API_KEY environment variable is not set."
    )


api_key_header = APIKeyHeader(
    name="x-api-key",
    auto_error=False,
)


def verify_api_key(
    x_api_key: str | None = Depends(api_key_header),
):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )


class MetricFilter(BaseModel):
    metric: str
    operator: str
    value: float


class SearchPlayersRequest(BaseModel):

    position: str | None = None

    availability: str = "all"

    sort_by: list[str] = Field(
        default_factory=lambda: [
            "avg_opportunities"
        ]
    )

    filters: list[MetricFilter] = Field(
        default_factory=list
    )

    last_n_weeks: int | None = None

    limit: int = 10


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "fantasy-research-api",
    }


@app.post(
    "/tools/search-players",
    dependencies=[
        Depends(verify_api_key)
    ],
)
def search_players_endpoint(
    request: SearchPlayersRequest,
):
    filters = [
        item.model_dump()
        for item in request.filters
    ]

    try:
        results = search_players(
            position=request.position,
            availability=request.availability,
            sort_by=request.sort_by,
            filters=filters,
            last_n_weeks=request.last_n_weeks,
            limit=request.limit,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "count": results.height,
        "rows": results.to_dicts(),
    }