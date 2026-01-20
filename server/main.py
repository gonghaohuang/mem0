import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from mem0 import Memory

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()


POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_COLLECTION_NAME = os.environ.get("POSTGRES_COLLECTION_NAME", "memories")

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "mem0graph")

MEMGRAPH_URI = os.environ.get("MEMGRAPH_URI", "bolt://localhost:7687")
MEMGRAPH_USERNAME = os.environ.get("MEMGRAPH_USERNAME", "memgraph")
MEMGRAPH_PASSWORD = os.environ.get("MEMGRAPH_PASSWORD", "mem0graph")

# LLM 和 Embedder 提供商配置 (支持: openai, gemini)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
EMBEDDER_PROVIDER = os.environ.get("EMBEDDER_PROVIDER", "openai")

# OpenAI 配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")  # 第三方 API 地址，如 https://api.gptsapi.net/v1

# Google Gemini 配置
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# 模型名称
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-2.0-flash" if LLM_PROVIDER == "gemini" else "gpt-4o-mini")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "models/text-embedding-004" if EMBEDDER_PROVIDER == "gemini" else "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "768" if EMBEDDER_PROVIDER == "gemini" else "1536"))

HISTORY_DB_PATH = os.environ.get("HISTORY_DB_PATH", "/app/history/history.db")
ENABLE_GRAPH = os.environ.get("ENABLE_GRAPH", "false").lower() == "true"  # 是否启用图数据库，默认关闭，设置为 true 可启用

# 构建 LLM 配置
def _build_llm_config():
    if LLM_PROVIDER == "gemini":
        return {
            "provider": "gemini",
            "config": {
                "api_key": GOOGLE_API_KEY,
                "temperature": 0.2,
                "model": LLM_MODEL,
            },
        }
    else:  # openai
        return {
            "provider": "openai",
            "config": {
                "api_key": OPENAI_API_KEY,
                "temperature": 0.2,
                "model": LLM_MODEL,
                **({"openai_base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
            },
        }


# 构建 Embedder 配置
def _build_embedder_config():
    if EMBEDDER_PROVIDER == "gemini":
        return {
            "provider": "gemini",
            "config": {
                "api_key": GOOGLE_API_KEY,
                "model": EMBEDDING_MODEL,
                "embedding_dims": EMBEDDING_DIMS,
            },
        }
    else:  # openai
        return {
            "provider": "openai",
            "config": {
                "api_key": OPENAI_API_KEY,
                "model": EMBEDDING_MODEL,
                **({"openai_base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
            },
        }


DEFAULT_CONFIG = {
    "version": "v1.1",
    "vector_store": {
        "provider": "pgvector",
        "config": {
            "host": POSTGRES_HOST,
            "port": int(POSTGRES_PORT),
            "dbname": POSTGRES_DB,
            "user": POSTGRES_USER,
            "password": POSTGRES_PASSWORD,
            "collection_name": POSTGRES_COLLECTION_NAME,
            "embedding_model_dims": EMBEDDING_DIMS,
        },
    },
    # 图数据库配置 - 可通过 ENABLE_GRAPH 环境变量禁用
    **({"graph_store": {
        "provider": "neo4j",
        "config": {"url": NEO4J_URI, "username": NEO4J_USERNAME, "password": NEO4J_PASSWORD},
    }} if ENABLE_GRAPH else {}),
    "llm": _build_llm_config(),
    "embedder": _build_embedder_config(),
    "history_db_path": HISTORY_DB_PATH,
}

logging.info(f"LLM Provider: {LLM_PROVIDER}, Model: {LLM_MODEL}")
logging.info(f"Embedder Provider: {EMBEDDER_PROVIDER}, Model: {EMBEDDING_MODEL}, Dims: {EMBEDDING_DIMS}")
logging.info(f"Graph database enabled: {ENABLE_GRAPH}")


MEMORY_INSTANCE = Memory.from_config(DEFAULT_CONFIG)

app = FastAPI(
    title="Mem0 REST APIs",
    description="A REST API for managing and searching memories for your AI Agents and Apps.",
    version="1.0.0",
)


class Message(BaseModel):
    role: str = Field(..., description="Role of the message (user or assistant).")
    content: str = Field(..., description="Message content.")


class MemoryCreate(BaseModel):
    messages: List[Message] = Field(..., description="List of messages to store.")
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query.")
    user_id: Optional[str] = None
    run_id: Optional[str] = None
    agent_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


@app.post("/configure", summary="Configure Mem0")
def set_config(config: Dict[str, Any]):
    """Set memory configuration."""
    global MEMORY_INSTANCE
    MEMORY_INSTANCE = Memory.from_config(config)
    return {"message": "Configuration set successfully"}


@app.post("/memories", summary="Create memories")
def add_memory(memory_create: MemoryCreate):
    """Store new memories."""
    if not any([memory_create.user_id, memory_create.agent_id, memory_create.run_id]):
        raise HTTPException(status_code=400, detail="At least one identifier (user_id, agent_id, run_id) is required.")

    params = {k: v for k, v in memory_create.model_dump().items() if v is not None and k != "messages"}
    try:
        response = MEMORY_INSTANCE.add(messages=[m.model_dump() for m in memory_create.messages], **params)
        return JSONResponse(content=response)
    except Exception as e:
        logging.exception("Error in add_memory:")  # This will log the full traceback
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories", summary="Get memories")
def get_all_memories(
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """Retrieve stored memories."""
    if not any([user_id, run_id, agent_id]):
        raise HTTPException(status_code=400, detail="At least one identifier is required.")
    try:
        params = {
            k: v for k, v in {"user_id": user_id, "run_id": run_id, "agent_id": agent_id}.items() if v is not None
        }
        return MEMORY_INSTANCE.get_all(**params)
    except Exception as e:
        logging.exception("Error in get_all_memories:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}", summary="Get a memory")
def get_memory(memory_id: str):
    """Retrieve a specific memory by ID."""
    try:
        return MEMORY_INSTANCE.get(memory_id)
    except Exception as e:
        logging.exception("Error in get_memory:")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", summary="Search memories")
def search_memories(search_req: SearchRequest):
    """Search for memories based on a query."""
    try:
        params = {k: v for k, v in search_req.model_dump().items() if v is not None and k != "query"}
        return MEMORY_INSTANCE.search(query=search_req.query, **params)
    except Exception as e:
        logging.exception("Error in search_memories:")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/memories/{memory_id}", summary="Update a memory")
def update_memory(memory_id: str, updated_memory: Dict[str, Any]):
    """Update an existing memory with new content.
    
    Args:
        memory_id (str): ID of the memory to update
        updated_memory (str): New content to update the memory with
        
    Returns:
        dict: Success message indicating the memory was updated
    """
    try:
        return MEMORY_INSTANCE.update(memory_id=memory_id, data=updated_memory)
    except Exception as e:
        logging.exception("Error in update_memory:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}/history", summary="Get memory history")
def memory_history(memory_id: str):
    """Retrieve memory history."""
    try:
        return MEMORY_INSTANCE.history(memory_id=memory_id)
    except Exception as e:
        logging.exception("Error in memory_history:")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memories/{memory_id}", summary="Delete a memory")
def delete_memory(memory_id: str):
    """Delete a specific memory by ID."""
    try:
        MEMORY_INSTANCE.delete(memory_id=memory_id)
        return {"message": "Memory deleted successfully"}
    except Exception as e:
        logging.exception("Error in delete_memory:")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memories", summary="Delete all memories")
def delete_all_memories(
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """Delete all memories for a given identifier."""
    if not any([user_id, run_id, agent_id]):
        raise HTTPException(status_code=400, detail="At least one identifier is required.")
    try:
        params = {
            k: v for k, v in {"user_id": user_id, "run_id": run_id, "agent_id": agent_id}.items() if v is not None
        }
        MEMORY_INSTANCE.delete_all(**params)
        return {"message": "All relevant memories deleted"}
    except Exception as e:
        logging.exception("Error in delete_all_memories:")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset", summary="Reset all memories")
def reset_memory():
    """Completely reset stored memories."""
    try:
        MEMORY_INSTANCE.reset()
        return {"message": "All memories reset"}
    except Exception as e:
        logging.exception("Error in reset_memory:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", summary="Redirect to the OpenAPI documentation", include_in_schema=False)
def home():
    """Redirect to the OpenAPI documentation."""
    return RedirectResponse(url="/docs")


# ==================== MemoryClient 兼容 API ====================
# 以下路由用于兼容 mem0 MemoryClient 的 API 格式，使 mem0-mcp 可以连接到自托管服务

class MemoryCreateV1(BaseModel):
    """MemoryClient 格式的请求体"""
    messages: List[Message] = Field(..., description="List of messages to store.")
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    app_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    enable_graph: Optional[bool] = False
    async_mode: Optional[bool] = True
    output_format: Optional[str] = "v1.1"


class SearchRequestV2(BaseModel):
    """MemoryClient v2 搜索格式"""
    query: str = Field(..., description="Search query.")
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    enable_graph: Optional[bool] = False


class GetMemoriesV2(BaseModel):
    """MemoryClient v2 获取记忆格式"""
    filters: Optional[Dict[str, Any]] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    enable_graph: Optional[bool] = False


def _extract_ids_from_filters(filters: Optional[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    """从 filters 中提取 user_id, agent_id, run_id"""
    result = {"user_id": None, "agent_id": None, "run_id": None}
    if not filters:
        return result
    
    # 处理 AND 格式: {"AND": [{"user_id": "xxx"}, ...]}
    if "AND" in filters:
        for condition in filters["AND"]:
            if isinstance(condition, dict):
                for key in ["user_id", "agent_id", "run_id"]:
                    if key in condition:
                        result[key] = condition[key]
    else:
        # 直接格式
        for key in ["user_id", "agent_id", "run_id"]:
            if key in filters:
                result[key] = filters[key]
    
    return result


@app.get("/v1/ping/", summary="Health check for MemoryClient")
def ping_v1():
    """MemoryClient 健康检查接口"""
    return {"status": "ok", "message": "Self-hosted Mem0 server is running"}


@app.post("/v1/memories/", summary="Create memories (MemoryClient compatible)")
def add_memory_v1(memory_create: MemoryCreateV1):
    """MemoryClient 兼容的添加记忆接口"""
    if not any([memory_create.user_id, memory_create.agent_id, memory_create.run_id]):
        raise HTTPException(status_code=400, detail="At least one identifier (user_id, agent_id, run_id) is required.")

    params = {k: v for k, v in memory_create.model_dump().items() 
              if v is not None and k not in ["messages", "enable_graph", "async_mode", "output_format", "app_id"]}
    try:
        response = MEMORY_INSTANCE.add(messages=[m.model_dump() for m in memory_create.messages], **params)
        return JSONResponse(content=response)
    except Exception as e:
        logging.exception("Error in add_memory_v1:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/memories/{memory_id}/", summary="Get a memory (MemoryClient compatible)")
def get_memory_v1(memory_id: str):
    """MemoryClient 兼容的获取单条记忆接口"""
    try:
        return MEMORY_INSTANCE.get(memory_id)
    except Exception as e:
        logging.exception("Error in get_memory_v1:")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/v1/memories/{memory_id}/", summary="Update a memory (MemoryClient compatible)")
def update_memory_v1(memory_id: str, updated_memory: Dict[str, Any]):
    """MemoryClient 兼容的更新记忆接口"""
    try:
        text = updated_memory.get("text")
        if text:
            return MEMORY_INSTANCE.update(memory_id=memory_id, data=text)
        return MEMORY_INSTANCE.update(memory_id=memory_id, data=updated_memory)
    except Exception as e:
        logging.exception("Error in update_memory_v1:")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/v1/memories/{memory_id}/", summary="Delete a memory (MemoryClient compatible)")
def delete_memory_v1(memory_id: str):
    """MemoryClient 兼容的删除单条记忆接口"""
    try:
        MEMORY_INSTANCE.delete(memory_id=memory_id)
        return {"message": "Memory deleted successfully"}
    except Exception as e:
        logging.exception("Error in delete_memory_v1:")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/v1/memories/", summary="Delete all memories (MemoryClient compatible)")
def delete_all_memories_v1(
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """MemoryClient 兼容的批量删除接口"""
    if not any([user_id, run_id, agent_id]):
        raise HTTPException(status_code=400, detail="At least one identifier is required.")
    try:
        params = {k: v for k, v in {"user_id": user_id, "run_id": run_id, "agent_id": agent_id}.items() if v is not None}
        MEMORY_INSTANCE.delete_all(**params)
        return {"message": "All relevant memories deleted"}
    except Exception as e:
        logging.exception("Error in delete_all_memories_v1:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/memories/{memory_id}/history/", summary="Get memory history (MemoryClient compatible)")
def memory_history_v1(memory_id: str):
    """MemoryClient 兼容的获取记忆历史接口"""
    try:
        return MEMORY_INSTANCE.history(memory_id=memory_id)
    except Exception as e:
        logging.exception("Error in memory_history_v1:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/entities/", summary="List entities (MemoryClient compatible)")
def list_entities_v1():
    """MemoryClient 兼容的列出实体接口"""
    try:
        # 本地 Memory 类没有 users() 方法，返回空结果
        return {"results": []}
    except Exception as e:
        logging.exception("Error in list_entities_v1:")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/v2/entities/{entity_type}/{entity_name}/", summary="Delete entity (MemoryClient compatible)")
def delete_entity_v2(entity_type: str, entity_name: str):
    """MemoryClient 兼容的删除实体接口"""
    try:
        params = {}
        if entity_type == "user":
            params["user_id"] = entity_name
        elif entity_type == "agent":
            params["agent_id"] = entity_name
        elif entity_type == "run":
            params["run_id"] = entity_name
        
        if params:
            MEMORY_INSTANCE.delete_all(**params)
        return {"message": "Entity deleted successfully"}
    except Exception as e:
        logging.exception("Error in delete_entity_v2:")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v2/memories/", summary="Get memories with filters (MemoryClient compatible)")
def get_memories_v2(
    request: GetMemoriesV2,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
):
    """MemoryClient 兼容的获取记忆接口 (v2)"""
    try:
        ids = _extract_ids_from_filters(request.filters)
        if not any(ids.values()):
            raise HTTPException(status_code=400, detail="At least one identifier is required in filters.")
        
        params = {k: v for k, v in ids.items() if v is not None}
        result = MEMORY_INSTANCE.get_all(**params)
        
        # 确保返回格式正确
        if isinstance(result, dict) and "results" in result:
            return result
        return {"results": result if isinstance(result, list) else []}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error in get_memories_v2:")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v2/memories/search/", summary="Search memories (MemoryClient compatible)")
def search_memories_v2(search_req: SearchRequestV2):
    """MemoryClient 兼容的搜索接口 (v2)"""
    try:
        ids = _extract_ids_from_filters(search_req.filters)
        if not any(ids.values()):
            raise HTTPException(status_code=400, detail="At least one identifier is required in filters.")
        
        params = {k: v for k, v in ids.items() if v is not None}
        if search_req.limit:
            params["limit"] = search_req.limit
            
        result = MEMORY_INSTANCE.search(query=search_req.query, **params)
        
        # 确保返回格式正确
        if isinstance(result, dict) and "results" in result:
            return result
        return {"results": result if isinstance(result, list) else []}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error in search_memories_v2:")
        raise HTTPException(status_code=500, detail=str(e))
