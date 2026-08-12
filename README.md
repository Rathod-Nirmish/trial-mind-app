# TrialMind

A multi-agent clinical research assistant that answers questions about clinical trials by retrieving and analyzing data from ClinicalTrials.gov. Exposes a Vue 3 web interface and an MCP (Model Context Protocol) server for Claude Desktop integration.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                  Frontend                   │
│         Vue 3 + TypeScript + Vite           │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │Explorations│ │  Corpus  │ │    Runs     │ │
│  └──────────┘ └──────────┘ └─────────────┘ │
└────────────────────┬────────────────────────┘
                     │ HTTP / SSE
┌────────────────────▼────────────────────────┐
│               FastAPI Backend               │
│  ┌──────────────────────────────────────┐   │
│  │           LangGraph Supervisor        │   │
│  │  ┌───────────┐  ┌─────────────────┐  │   │
│  │  │ Retriever │  │    Analyzer     │  │   │
│  │  └───────────┘  └─────────────────┘  │   │
│  │         ┌──────────────────┐         │   │
│  │         │ Citation Checker │         │   │
│  │         └──────────────────┘         │   │
│  └──────────────────────────────────────┘   │
└───────┬──────────────────────┬──────────────┘
        │                      │
┌───────▼──────────┐  ┌────────▼──────────────┐
│  Supabase (pgvec) │  │   Google Gemini /     │
│  BM25 + Semantic  │  │   Anthropic Claude    │
│       Search      │  │   (LLM providers)     │
└───────────────────┘  └───────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, TypeScript, Vite, TailwindCSS, Reka-ui, Vue Router |
| Backend | Python 3.11, FastAPI, LangGraph, LangChain-core, Pydantic v2 |
| LLMs | Google Gemini 2.0 Flash (primary), Anthropic Claude Sonnet 4.6 (premium) |
| Database | Supabase (PostgreSQL 15+ with pgvector), SQLite (LLM cache) |
| Migrations | Alembic |
| Package managers | `uv` (Python), `pnpm` (JavaScript) |

---

## Features

- **Hybrid RAG Search** — BM25 full-text search combined with vector semantic search via Reciprocal Rank Fusion
- **Multi-Agent System** — LangGraph supervisor coordinating Retriever, Analyzer, and Citation-Checker agents
- **Citation Verification** — LLM-based entailment checking with deterministic validation fallback
- **SSE Streaming** — Real-time agent responses streamed to the UI via Server-Sent Events
- **MCP Server** — Expose the agent as a tool for Claude Desktop integration
- **Mock API Mode** — Develop the frontend without a running backend via `VITE_USE_MOCK_API`
- **Cost Control** — Unified LLM client with SQLite caching and per-request budget enforcement

---

## Project Structure

```
trial-mind-app/
├── backend/
│   └── trialmind/
│       ├── agents/          # Retriever, Analyzer, Citation-Checker agents
│       ├── api/             # FastAPI routes and SSE endpoints
│       ├── graph/           # LangGraph supervisor and state definitions
│       ├── ingestion/       # ClinicalTrials.gov data ingestion pipeline
│       ├── mcp/             # MCP server for Claude Desktop
│       └── core/            # Shared config, LLM client, caching
├── frontend/
│   └── src/
│       ├── components/      # Reusable Vue components
│       ├── views/           # Page-level components
│       ├── services/        # API client and mock API
│       └── composables/     # Vue composables (shared logic)
├── docs/
│   └── superpowers/specs/   # Design specs and implementation plans
└── alembic/                 # Database migrations
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ and `pnpm`
- [`uv`](https://github.com/astral-sh/uv) Python package manager
- Supabase project with `pgvector` and full-text search extensions enabled

### Environment Variables

Create a `.env` file in `backend/`:

```env
# LLM providers
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GROQ_API_KEY=your_groq_api_key          # optional

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=postgresql://...
```

Create a `.env` file in `frontend/`:

```env
VITE_API_BASE=http://localhost:8000
VITE_USE_MOCK_API=false                 # set to true for frontend-only development
```

---

## Running Locally

### Backend

```bash
cd backend
uv sync                          # install dependencies
uv run alembic upgrade head      # run migrations
python -m trialmind.api.main     # starts on http://localhost:8000
```

### Frontend

```bash
cd frontend
pnpm install
pnpm run dev                     # starts on http://localhost:5173
```

### Frontend only (mock API)

```bash
# In frontend/.env
VITE_USE_MOCK_API=true

cd frontend
pnpm run dev
```

---

## Usage

| View | Description |
|------|-------------|
| **Explorations** | Ask natural-language questions about clinical trials; responses stream in real time with inline citations |
| **Corpus** | Ingest and manage clinical trial documents from ClinicalTrials.gov |
| **Runs** | Run and review automated evaluation benchmarks |
| **Workbench** | Configure and tune agent behavior |

---

## MCP Server (Claude Desktop)

TrialMind exposes an MCP server so the agent can be used directly as a tool inside Claude Desktop.

```bash
cd backend
python -m trialmind.mcp.server
```

Add the server to your Claude Desktop MCP config to start querying clinical trials from within Claude conversations.
