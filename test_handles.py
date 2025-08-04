#!/usr/bin/env python3
"""
Simple tests for the three _handle functions in main.py
"""

import asyncio
import sys
import os

# Add the server directory to the path so we can import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "server"))

from main import _handle_search, _handle_fetch, _handle_get_paper_prompt


async def test_handle_search():
    """Test _handle_search with a simple query"""
    print("Testing _handle_search...")

    try:
        # Test with valid arguments
        results = await _handle_search({"query": "machine learning"})
        print(f"✓ Search returned {len(results)} results")

        if results:
            first_result = results[0]
            print(f"  Search results: {first_result.text[:100]}...")
            print(f"  Result type: {first_result.type}")

        # Test with missing arguments
        try:
            await _handle_search({})
            print("✗ Should have raised ValueError for missing query")
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")

    except Exception as e:
        print(f"✗ _handle_search failed: {e}")
        return False

    return True


async def test_handle_fetch():
    """Test _handle_fetch with a known arXiv ID"""
    print("\nTesting _handle_fetch...")

    try:
        # Use a well-known arXiv paper (BERT)
        arxiv_id = "1810.04805"

        # Test with valid arguments
        results = await _handle_fetch({"id": arxiv_id})
        print(f"✓ Fetch returned {len(results)} document(s)")

        if results:
            content = results[0]
            print(f"  Content type: {content.type}")
            print(f"  Content text length: {len(content.text)} characters")
            print(
                f"  Has LaTeX content: {'\\begin' in content.text or '\\section' in content.text}"
            )
            # Check metadata for document info
            if hasattr(content, "metadata") and content.metadata:
                print(f"  Document ID: {content.metadata.get('id', 'N/A')}")
                print(
                    f"  Document title: {content.metadata.get('title', 'N/A')[:50]}..."
                )

        # Test with missing arguments
        try:
            await _handle_fetch({})
            print("✗ Should have raised ValueError for missing id")
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")

    except Exception as e:
        print(f"✗ _handle_fetch failed: {e}")
        return False

    return True


async def test_handle_get_paper_prompt():
    """Test _handle_get_paper_prompt with a known arXiv ID"""
    print("\nTesting _handle_get_paper_prompt...")

    try:
        # Use the same well-known arXiv paper
        arxiv_id = "1810.04805"

        # Test with valid arguments
        results = await _handle_get_paper_prompt({"arxiv_id": arxiv_id})
        print(f"✓ get_paper_prompt returned {len(results)} text content(s)")

        if results:
            content = results[0]
            print(f"  Content type: {content.type}")
            print(f"  Content text length: {len(content.text)} characters")
            print(
                f"  Has LaTeX content: {'\\begin' in content.text or '\\section' in content.text}"
            )
            print(f"  Has instructions: {'IMPORTANT INSTRUCTIONS' in content.text}")

        # Test with missing arguments
        try:
            await _handle_get_paper_prompt({})
            print("✗ Should have raised ValueError for missing arxiv_id")
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")

    except Exception as e:
        print(f"✗ _handle_get_paper_prompt failed: {e}")
        return False

    return True


async def main():
    """Run all tests"""
    print("Running basic tests for _handle functions...\n")

    tests = [test_handle_search(), test_handle_fetch(), test_handle_get_paper_prompt()]

    results = await asyncio.gather(*tests, return_exceptions=True)

    success_count = sum(1 for r in results if r is True)
    total_count = len(results)

    print(f"\n{'='*50}")
    print(f"Test Results: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("✓ All basic tests passed! No major bugs detected.")
    else:
        print("✗ Some tests failed. Check the output above.")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  Test {i+1} exception: {result}")


if __name__ == "__main__":
    asyncio.run(main())
