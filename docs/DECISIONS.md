

# DECISIONS.md — Cloud Milestone Addendum

Append these entries to the existing project decision log.

---

## Decision: Use FastAPI/OpenAPI as the stable service boundary

**Status:** Accepted

The deterministic analytics layer is exposed through FastAPI rather than allowing the Foundry agent or frontend to access DuckDB directly.

**Why:**

- creates a stable contract between UI, AI, analytics, and storage
- gives request validation
- automatically produces OpenAPI
- makes the storage implementation replaceable later
- lets Foundry call deterministic functions as tools

---

## Decision: Use Docker + Azure Container Apps for the backend

**Status:** Accepted

The backend is packaged as a Linux Docker image and deployed to Azure Container Apps.

**Why:**

- reproducible runtime
- no VM management
- clear local-to-cloud deployment artifact
- appropriate fit for a small FastAPI service
- production-shaped Azure experience without excessive infrastructure

---

## Decision: Build Docker images locally instead of using ACR Tasks

**Status:** Accepted due to subscription constraint

Azure for Students rejected ACR Tasks with `TasksOperationsNotAllowed`.

The project therefore uses:

```text
local Docker build
→ docker push
→ Azure Container Registry
→ Azure Container Apps
```

This changes the build location, not the runtime architecture.

---

## Decision: Use user-assigned managed identity for ACR image pulls

**Status:** Accepted

The Container App uses a user-assigned identity with the `AcrPull` role.

**Why:**

- avoids registry usernames/passwords
- uses Azure-native workload identity
- separates infrastructure authentication from app-level authentication

---

## Decision: Protect the analytics endpoint with an API key

**Status:** Accepted for the current development architecture

`POST /tools/search-players` requires `x-api-key`.

FastAPI validates the credential using `APIKeyHeader`.

**Secret storage:**

- Azure Container Apps secret stores the backend copy
- Foundry custom connection stores the caller copy
- GitHub/source code stores neither value

**Future note:** end-user authentication will be a separate concern.

---

## Decision: Expose a curated agent-facing OpenAPI schema

**Status:** Accepted

The Foundry tool exposes only the deterministic operation the agent needs rather than handing the agent every possible backend route.

**Why:**

- smaller tool context
- clearer enums and valid arguments
- less room for model misuse
- easier agent instructions
- easier future versioning

---

## Decision: Treat tool attachment as part of agent deployment

**Status:** Accepted

Creating a custom OpenAPI tool does not guarantee that the active agent version can use it.

The operational checklist now includes:

```text
create / configure tool
→ attach tool to agent
→ save agent version
→ test
→ inspect trace
```

This decision came from a real failure where the model answered without any tool-call span.

---

## Decision: Never mask tool failure with fabricated data

**Status:** Accepted

Agent instructions explicitly prohibit placeholder players, invented statistics, or unsupported recommendations.

If a tool fails or evidence is missing, the agent should report the limitation.

Foundry traces are part of the debugging workflow.

---

## Decision: Start frontend after the first complete cloud vertical slice

**Status:** Accepted

Frontend development begins once the following path works:

```text
natural language
→ Foundry agent
→ OpenAPI tool
→ Azure FastAPI
→ deterministic analytics
→ evidence-backed answer
```

This milestone is now complete.

Cloud SQL, multi-league sync, injury/news grounding, advanced play-by-play features, and predictive modeling are important next phases, but they are not prerequisites for beginning the UI.

---

## Decision: Use relational storage for core app data unless a different workload justifies otherwise

**Status:** Directional / future

League, roster, user, player, week, matchup, and ownership entities are naturally relational.

When the project moves beyond the baked DuckDB snapshot, Azure SQL or PostgreSQL should be evaluated before choosing a document database simply for technology breadth.

Cosmos DB remains an option only if a document/event workload justifies it.

---

## Decision: Use hybrid grounding, not “RAG for everything”

**Status:** Directional / future

Structured numeric facts should come from SQL/tools.

Retrieval/vector search is more appropriate for unstructured context such as:

- injury reports
- beat-reporter notes
- news
- coach comments
- qualitative weather/context

Future architecture should combine deterministic structured evidence with retrieval where the data type actually benefits from it.

---

## Decision: Use async selectively

**Status:** Accepted principle

Do not add `async/await` merely to look modern.

Use async for network-bound I/O where concurrency improves latency, such as external API calls.

Keep CPU-bound dataframe/analytics logic synchronous unless profiling shows a real reason to change it.
