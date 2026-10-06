# Fantasy Research Agent — Status

**Last updated:** October 5, 2026  
**Current milestone:** End-to-end cloud backend vertical slice complete  
**Next major milestone:** Frontend

## What works now

- Sleeper league ingestion and league ownership mapping.
- nflverse / nflreadpy weekly player data, schedules, snap counts, and roster status.
- Unified DuckDB analytics tables including `player_week` and `league_ownership`.
- Generic deterministic `search_players()` research tool.
- Schedule-aware trend guardrails that avoid treating partial or immature data as reliable trends.
- Foundry Local structured tool-calling development harness.
- FastAPI backend with Swagger/OpenAPI documentation.
- Dockerized backend validated locally.
- Versioned Docker images pushed to Azure Container Registry.
- Azure Container App deployed with public HTTPS ingress.
- User-assigned managed identity with `AcrPull` for private registry access.
- API-key authentication on the analytics endpoint.
- API key stored as an Azure Container Apps secret, not in source control.
- Microsoft Foundry project with GPT-4.1 mini.
- Foundry custom connection storing the `x-api-key` credential as a secret.
- Custom OpenAPI tool `fantasy_player_research` attached to the active agent.
- Foundry traces available for debugging agent/tool behavior.
- First successful cloud query completed:
  natural language → Foundry → OpenAPI → Azure Container Apps → FastAPI → DuckDB → evidence → answer.

## Current deployment shape

```text
Local source + DuckDB snapshot
        ↓
Docker build
        ↓
Azure Container Registry
        ↓  AcrPull via managed identity
Azure Container Apps
        ↓
secured FastAPI endpoint
        ↑
Foundry custom connection + OpenAPI tool
        ↑
GPT-4.1 mini agent
```

## Current limitations

1. **Cloud data is a snapshot.**  
   The deployed container currently carries the DuckDB database that existed at build time. The cloud API is not yet continuously refreshed.

2. **Single configured league context.**  
   The current backend is effectively scoped to the one refreshed Sleeper league. Multi-league user selection is not implemented yet.

3. **Tool surface is intentionally narrow.**  
   The first cloud tool exposes player search/usage research. Compare-player, roster-analysis, trade, matchup, and richer projection tools are still future work.

4. **No live injury/news/weather grounding yet.**  
   Current answers are based on structured league/NFL data in the snapshot.

5. **No predictive model yet.**  
   Current analytics are descriptive and usage-based. The project should not present them as true future projections.

6. **No production user authentication/accounts yet.**  
   The API-key layer protects the agent tool endpoint, but the app does not yet have end-user auth.

## Immediate next milestone: frontend

Build the first real UI against the existing backend rather than mocked data.

Initial frontend scope:

- league/team overview
- research/chat panel
- evidence table
- player cards
- basic charts
- waiver/research result views

The frontend should render numbers returned by deterministic tools rather than asking the LLM to invent chart data.

## Backend phases after frontend

### Cloud-refreshable data layer
- move beyond the baked DuckDB snapshot
- introduce Azure-backed persistence where justified
- add scheduled/background league syncing
- keep dashboard requests decoupled from external API calls

### Multi-league + caching
- user → league → roster relationships
- multiple Sleeper leagues per account
- cached/scheduled refreshes
- indexed relational queries

### Advanced football analytics
- nflverse play-by-play ingestion
- opportunity share
- red-zone / goal-line usage
- target and rushing shares
- expected-value features where data supports them

### Live context grounding
- injuries
- transactions
- weather
- news / beat-reporter context
- hybrid structured tools + retrieval for unstructured text

### Predictive modeling
- projections
- backtesting
- feature engineering
- model evaluation
- eventually LightGBM / XGBoost or similar models if justified

### Observability and evaluation
- Application Insights / tracing
- Foundry evaluations
- tool-call success metrics
- latency / failure monitoring

## Important engineering notes

- Azure for Students blocked ACR Tasks, so images are built locally and pushed to ACR.
- The Container App uses managed identity for registry access rather than registry passwords.
- Secrets are stored in Azure/Foundry secret stores and are not committed to Git.
- A Foundry trace exposed an early orchestration failure where the model answered without calling the tool.
- Creating an OpenAPI tool and attaching/saving it on the active agent are separate steps.
- GPT-4.1 mini development quota is currently set to 50K TPM. This is a rate-limit allocation, not continuous token usage.

## Definition of the current milestone

The backend is not “finished,” but it has crossed the threshold required to begin frontend development:

> A real user question can now reach a cloud-hosted AI agent, trigger a secured deterministic analytics API, query league-specific data, and return evidence-backed results.
