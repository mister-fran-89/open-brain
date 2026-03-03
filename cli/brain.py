#!/usr/bin/env python3
"""Open Brain CLI - capture and query your knowledge base."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


DEFAULT_HOST = "http://localhost:8000"


async def capture(args):
    """Capture text to the brain."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{args.host}/api/capture",
            json={"text": args.text, "source": "cli"},
            timeout=30.0,
        )

    if response.status_code == 200:
        data = response.json()
        print(f"Captured: {data['title']}")
        print(f"  Category: {data['category']}")
        print(f"  Confidence: {data['confidence']:.0%}")
        print(f"  ID: {data['id']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        sys.exit(1)


async def query(args):
    """Query the brain."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{args.host}/api/query",
            json={"question": args.question},
            timeout=60.0,
        )

    if response.status_code == 200:
        data = response.json()
        print(data["answer"])
        if data["sources"]:
            print("\n---\nSources:")
            for source in data["sources"]:
                print(f"  - {source['title']} ({source['category']})")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        sys.exit(1)


async def search(args):
    """Search the brain."""
    params = {}
    if args.category:
        params["category"] = args.category
    if args.tags:
        params["tags"] = args.tags
    if args.text:
        params["text"] = args.text

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{args.host}/api/search",
            params=params,
            timeout=30.0,
        )

    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} items:\n")
        for item in data["items"]:
            print(f"[{item['category']}] {item['title']}")
            if item["content"]:
                print(f"  {item['content'][:100]}...")
            print()
    else:
        print(f"Error: {response.status_code}")
        sys.exit(1)


async def digest(args):
    """Generate a digest."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{args.host}/api/digest",
            json={"period": args.period},
            timeout=60.0,
        )

    if response.status_code == 200:
        data = response.json()
        print(data["content"])
        print(f"\n---\n{len(data['items'])} items included")
    else:
        print(f"Error: {response.status_code}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Open Brain - Personal Knowledge System",
        prog="brain",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"API host (default: {DEFAULT_HOST})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Capture command
    capture_parser = subparsers.add_parser("capture", help="Capture text")
    capture_parser.add_argument("text", help="Text to capture")
    capture_parser.set_defaults(func=capture)

    # Query command
    query_parser = subparsers.add_parser("query", help="Ask a question")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.set_defaults(func=query)

    # Search command
    search_parser = subparsers.add_parser("search", help="Search items")
    search_parser.add_argument("--category", "-c", help="Filter by category")
    search_parser.add_argument("--tags", "-t", help="Filter by tags (comma-separated)")
    search_parser.add_argument("--text", "-q", help="Full-text search")
    search_parser.set_defaults(func=search)

    # Digest command
    digest_parser = subparsers.add_parser("digest", help="Generate digest")
    digest_parser.add_argument(
        "--period", "-p",
        default="daily",
        choices=["daily", "weekly"],
        help="Digest period",
    )
    digest_parser.set_defaults(func=digest)

    args = parser.parse_args()
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
