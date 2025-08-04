#!/usr/bin/env python3
"""
ArXiv LaTeX MCP Server

This server provides tools to fetch and process arXiv papers' LaTeX source code
for better mathematical expression interpretation.
"""

import asyncio
import logging
from typing import Any
import xml.etree.ElementTree as ET

import aiohttp
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.stdio import stdio_server
from pydantic import BaseModel

from arxiv_to_prompt import process_latex_source


# Custom models for structured data
class SearchResultModel(BaseModel):
    id: str
    title: str
    text: str
    url: str


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arxiv-latex-mcp")

# Create server instance
server = Server("arxiv-latex-mcp")

# ArXiv API URL for search
ARXIV_API_URL = "https://export.arxiv.org/api/query?search_query={}&max_results=10"


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="search",
            description="Search arXiv by free-text query and return matching papers",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text search terms"}
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="fetch",
            description="Retrieve the full LaTeX source (flattened) for a specific arXiv paper",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The document id returned by the search tool (arXiv ID, e.g. '2403.12345')",
                    }
                },
                "required": ["id"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Handle tool calls."""
    if name == "search":
        return await _handle_search(arguments)
    elif name == "fetch":
        return await _handle_fetch(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _handle_search(args: dict[str, Any]) -> list[types.TextContent]:
    """Handle search tool calls."""
    if not args or "query" not in args:
        raise ValueError("Missing required argument: query")
    query = args["query"]

    async with aiohttp.ClientSession() as session:
        async with session.get(ARXIV_API_URL.format(query)) as resp:
            data = await resp.text()

    # Parse Atom XML (very small, fast)
    root = ET.fromstring(data)
    results: list[SearchResultModel] = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        arxiv_id = entry.find("{http://www.w3.org/2005/Atom}id").text.split("/")[-1]
        title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
        summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
        url = f"https://arxiv.org/abs/{arxiv_id}"

        results.append(
            SearchResultModel(
                id=arxiv_id,
                title=title,
                text=summary[:500] + ("…" if len(summary) > 500 else ""),
                url=url,
            )
        )

    # Format results as text content
    if not results:
        return [
            types.TextContent(type="text", text="No papers found for the given query.")
        ]

    formatted_results = "Search Results:\n\n"
    for result in results:
        formatted_results += f"ID: {result.id}\n"
        formatted_results += f"Title: {result.title}\n"
        formatted_results += f"Summary: {result.text}\n"
        formatted_results += f"URL: {result.url}\n\n"

    return [types.TextContent(type="text", text=formatted_results)]


async def _handle_fetch(args: dict[str, Any]) -> list[types.TextContent]:
    """Handle fetch tool calls."""
    if not args or "id" not in args:
        raise ValueError("Missing required argument: id")
    arxiv_id = args["id"]

    logger.info(f"Fetching & processing arXiv paper: {arxiv_id}")
    try:
        flattened = process_latex_source(arxiv_id)

        instructions = (
            "\n\nIMPORTANT INSTRUCTIONS FOR RENDERING:\n"
            "When discussing this paper, please use dollar sign notation ($...$) "
            "for inline equations and double dollar signs ($...$) for display "
            "equations when providing responses that include LaTeX mathematical expressions."
        )

        return [
            types.TextContent(
                type="text",
                text=flattened + instructions,
                metadata={
                    "id": arxiv_id,
                    "title": f"arXiv:{arxiv_id}",
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "source": "arXiv",
                },
            )
        ]
    except Exception as exc:
        logger.exception("Error processing arXiv paper %s", arxiv_id)
        return [
            types.TextContent(
                type="text",
                text=str(exc),
                metadata={
                    "id": arxiv_id,
                    "title": f"Error: {arxiv_id}",
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                },
            )
        ]


async def main():
    """Main entry point for the server."""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="arxiv-latex-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
