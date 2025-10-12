#!/usr/bin/env python3
"""Demo script showing how to use the database history and analytics API.

This script demonstrates how to interact with the GraphQL database API
to query scan history, statistics, and corruption trends.

Requirements:
    - API server must be running (python -m uvicorn src.api.app:create_app --factory)
    - Database must be populated with scan data

Usage:
    python examples/database_api_demo.py
"""

import json

import requests


def execute_graphql_query(url: str, query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL query against the API.

    Args:
        url: GraphQL endpoint URL
        query: GraphQL query string
        variables: Optional query variables

    Returns:
        Response data from the API
    """
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def demo_database_stats(api_url: str) -> None:
    """Demo database statistics query."""
    print("\n" + "=" * 70)
    print("Database Statistics Demo")
    print("=" * 70)

    query = """
    query {
        databaseStats {
            totalScans
            totalFiles
            corruptFiles
            healthyFiles
            oldestScan
            newestScan
            databaseSizeBytes
        }
    }
    """

    result = execute_graphql_query(api_url, query)
    stats = result.get("data", {}).get("databaseStats", {})

    if stats:
        print(f"\nTotal Scans: {stats.get('totalScans', 0)}")
        print(f"Total Files: {stats.get('totalFiles', 0)}")
        print(f"Corrupt Files: {stats.get('corruptFiles', 0)}")
        print(f"Healthy Files: {stats.get('healthyFiles', 0)}")
        print(f"Database Size: {stats.get('databaseSizeBytes', 0)} bytes")
    else:
        print("\nNo statistics available")


def demo_scan_history(api_url: str) -> None:
    """Demo scan history query."""
    print("\n" + "=" * 70)
    print("Scan History Demo (Last 5 Scans)")
    print("=" * 70)

    query = """
    query {
        scanHistory(limit: 5) {
            id
            directory
            scanMode
            startedAt
            completedAt
            totalFiles
            corruptFiles
            healthyFiles
            successRate
        }
    }
    """

    result = execute_graphql_query(api_url, query)
    scans = result.get("data", {}).get("scanHistory", [])

    if scans:
        for scan in scans:
            print(f"\nScan ID: {scan['id']}")
            print(f"  Directory: {scan['directory']}")
            print(f"  Mode: {scan['scanMode']}")
            print(f"  Total Files: {scan['totalFiles']}")
            print(f"  Corrupt: {scan['corruptFiles']}")
            print(f"  Healthy: {scan['healthyFiles']}")
            print(f"  Success Rate: {scan['successRate']:.2f}%")
    else:
        print("\nNo scan history available")


def demo_corruption_trend(api_url: str, directory: str = "/test/videos") -> None:
    """Demo corruption trend query."""
    print("\n" + "=" * 70)
    print(f"Corruption Trend Demo for {directory}")
    print("=" * 70)

    query = """
    query GetTrend($directory: String!, $days: Int!) {
        corruptionTrend(directory: $directory, days: $days) {
            scanDate
            corruptFiles
            totalFiles
            corruptionRate
        }
    }
    """

    variables = {"directory": directory, "days": 30}

    result = execute_graphql_query(api_url, query, variables)
    trend_data = result.get("data", {}).get("corruptionTrend", [])

    if trend_data:
        print("\nDate       | Total Files | Corrupt Files | Corruption Rate")
        print("-" * 60)
        for data in trend_data:
            print(
                f"{data['scanDate']:<10} | "
                f"{data['totalFiles']:>11} | "
                f"{data['corruptFiles']:>13} | "
                f"{data['corruptionRate']:>14.2f}%"
            )
    else:
        print("\nNo corruption trend data available")


def demo_database_query(api_url: str) -> None:
    """Demo database query with filters."""
    print("\n" + "=" * 70)
    print("Database Query Demo (Corrupt Files)")
    print("=" * 70)

    query = """
    query GetCorruptFiles($limit: Int!) {
        databaseQuery(filter: {isCorrupt: true, limit: $limit}) {
            id
            filename
            fileSize
            confidence
            scanMode
            status
        }
    }
    """

    variables = {"limit": 10}

    result = execute_graphql_query(api_url, query, variables)
    files = result.get("data", {}).get("databaseQuery", [])

    if files:
        print(f"\nFound {len(files)} corrupt files:")
        for file in files:
            print(f"\nFile: {file['filename']}")
            print(f"  Size: {file['fileSize']} bytes")
            print(f"  Confidence: {file['confidence']:.2f}")
            print(f"  Scan Mode: {file['scanMode']}")
            print(f"  Status: {file['status']}")
    else:
        print("\nNo corrupt files found in database")


def demo_combined_query(api_url: str) -> None:
    """Demo combined query for dashboard overview."""
    print("\n" + "=" * 70)
    print("Dashboard Overview Demo")
    print("=" * 70)

    query = """
    query {
        databaseStats {
            totalScans
            totalFiles
            corruptFiles
            healthyFiles
        }
        scanHistory(limit: 3) {
            id
            directory
            corruptFiles
            successRate
        }
    }
    """

    result = execute_graphql_query(api_url, query)
    data = result.get("data", {})

    print("\nDatabase Overview:")
    stats = data.get("databaseStats", {})
    if stats:
        print(f"  Total Scans: {stats.get('totalScans', 0)}")
        print(f"  Total Files: {stats.get('totalFiles', 0)}")
        print(f"  Corrupt Files: {stats.get('corruptFiles', 0)}")

    print("\nRecent Scans:")
    scans = data.get("scanHistory", [])
    for scan in scans:
        print(f"  Scan {scan['id']}: {scan['directory']}")
        print(f"    Corrupt: {scan['corruptFiles']}, "
              f"Success: {scan['successRate']:.2f}%")


def main():
    """Run all demo queries."""
    # API endpoint (adjust if needed)
    api_url = "http://localhost:8000/graphql"

    print("\n" + "=" * 70)
    print("Corrupt Video Inspector - Database API Demo")
    print("=" * 70)
    print(f"\nConnecting to: {api_url}")
    print("\nNote: Make sure the API server is running and the database")
    print("      contains some scan data before running this demo.")

    try:
        # Run demo queries
        demo_database_stats(api_url)
        demo_scan_history(api_url)
        demo_corruption_trend(api_url)
        demo_database_query(api_url)
        demo_combined_query(api_url)

        print("\n" + "=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)

    except requests.exceptions.ConnectionError:
        print("\n" + "=" * 70)
        print("ERROR: Could not connect to API server")
        print("=" * 70)
        print("\nPlease start the API server first:")
        print("  python -m uvicorn src.api.app:create_app --factory --reload")
        print("\nOr using Docker:")
        print("  docker compose --profile api up")

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"ERROR: {e}")
        print("=" * 70)


if __name__ == "__main__":
    main()
