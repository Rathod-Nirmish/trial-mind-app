from __future__ import annotations
import asyncio
import sys
import json

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ListToolsResult,
    CallToolRequestParams,
    CallToolResult,
    PaginatedRequestParams,
)

from trialmind.db import hybrid_search
from trialmind.ingestion.embed import embed_query
from trialmind.graph.supervisor import run as run_graph

server = Server("trialmind")

TOOLS = [
    Tool(
        name="search_trials",
        description="Semantic + keyword search over the ingested clinical trials corpus.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k": {"type": "integer", "default": 8},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="analyze_question",
        description="Multi-agent analysis of a clinical question with cited answer.",
        inputSchema={
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    ),
]


async def _tool_search_trials(args: dict) -> list[dict]:
    query = args["query"]
    k = int(args.get("k", 8))
    emb = await embed_query(query)
    hits = await hybrid_search(query, emb, k=k)
    return [h.model_dump() for h in hits]


async def _tool_analyze_question(args: dict) -> dict:
    question = args["question"]
    final = await run_graph(question)
    return {
        "answer": final.draft_answer,
        "citations": [c.model_dump() for c in final.chunks],
        "check_ok": bool(final.check_result and final.check_result.ok),
        "issues": final.check_result.issues if final.check_result else [],
    }


async def _handle_list_tools(_params: PaginatedRequestParams | None) -> ListToolsResult:
    return ListToolsResult(tools=TOOLS)


async def _handle_call_tool(params: CallToolRequestParams) -> CallToolResult:
    name = params.name
    args = params.arguments or {}
    if name == "search_trials":
        payload = await _tool_search_trials(args)
    elif name == "analyze_question":
        payload = await _tool_analyze_question(args)
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"unknown tool: {name}")],
            isError=True,
        )
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(payload, indent=2))])


server.add_request_handler("tools/list", PaginatedRequestParams, _handle_list_tools)
server.add_request_handler("tools/call", CallToolRequestParams, _handle_call_tool)


async def _main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
