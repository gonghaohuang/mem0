# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Environment setup
make install          # Create hatch environment
make install_all      # Install all optional dependencies (vector stores, LLMs, etc.)

# Development
make format           # Format with ruff
make sort             # Sort imports with isort
make lint             # Lint with ruff
make lint-fix         # Auto-fix lint issues

# Testing
make test             # Run tests with default Python
make test-py-3.11     # Run tests on specific Python version
pytest tests/test_memory.py::TestClass::test_method -v  # Single test

# Build
make build            # Build distribution packages
make docs             # Run Mintlify docs dev server (cd docs && mintlify dev)
```

Pre-commit hooks: `pre-commit install` (runs ruff + isort automatically)

## Architecture

Mem0 is a long-term memory layer for AI agents. It stores, retrieves, and manages memories using a combination of vector databases, graph databases, and SQL.

### Core Components

**`mem0/`** - Core Python package:
- `memory/main.py` — Primary `Memory` and `AsyncMemory` classes; all CRUD operations live here
- `memory/graph_memory.py`, `memgraph_memory.py`, `kuzu_memory.py` — Graph-based memory backends
- `configs/` — Pydantic config classes: `MemoryConfig`, `LlmConfig`, `VectorStoreConfig`, etc.
- `utils/factory.py` — Factory pattern: `EmbedderFactory`, `LlmFactory`, `VectorStoreFactory`, `GraphStoreFactory`, `RerankerFactory`
- `client/main.py` — REST client (`MemoryClient`, `AsyncMemoryClient`) for the hosted API

**Plugin categories** (each with ~15-26 implementations):
- `vector_stores/` — Qdrant (default), Pinecone, Weaviate, Chroma, FAISS, pgvector, Milvus, Redis, etc.
- `llms/` — OpenAI, Anthropic, Gemini, Azure, Bedrock, Groq, Ollama, LiteLLM, etc.
- `embeddings/` — OpenAI, HuggingFace, FastEmbed, Ollama, Bedrock, etc.
- `graphs/` — Neo4j, Memgraph, Kuzu, Neptune
- `reranker/` — Cohere, HuggingFace, Sentence Transformers, LLM-based, Zero Entropy

**`server/`** — FastAPI REST API with Docker Compose (PostgreSQL + Neo4j/Memgraph)

**`mem0-ts/`** — TypeScript/Node.js SDK

### Data Flow

1. `Memory.add(messages)` → LLM extracts facts → embeddings generated → stored in vector store
2. `Memory.search(query)` → query embedded → nearest neighbors retrieved from vector store → optionally reranked
3. Graph memory runs in parallel when enabled: extracts entities/relationships → stored in graph DB
4. SQLite tracks memory history (`history_db_path`)

### Configuration Pattern

All backends are selected via config, not imports:
```python
from mem0 import Memory
config = {
    "vector_store": {"provider": "qdrant", "config": {...}},
    "llm": {"provider": "openai", "config": {"model": "gpt-4o"}},
    "embedder": {"provider": "openai", "config": {...}},
    "graph_store": {"provider": "neo4j", "config": {...}},  # optional
}
m = Memory.from_config(config)
```

Factories in `utils/factory.py` dynamically import and instantiate the correct class based on `provider` string.

### Memory Scoping

Memories are scoped by: `user_id`, `agent_id`, `run_id` — any combination can be used to namespace memories.

## Key Files

- `mem0/__init__.py` — Public API exports
- `mem0/memory/main.py` — Core memory logic (large file, ~103KB)
- `mem0/configs/base.py` — `MemoryConfig` and all sub-configs
- `pyproject.toml` — Dependencies, optional extras, hatch env definitions
- `server/docker-compose.yaml` — Local server stack
