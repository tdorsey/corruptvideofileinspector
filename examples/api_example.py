"""Example script demonstrating GraphQL API usage.

This script shows how to interact with the Corrupt Video Inspector GraphQL API
to start scans and retrieve results programmatically.

Requirements:
    pip install requests

Usage:
    # Make sure the API is running first:
    # make run-api  # or docker compose --profile api up

    python examples/api_example.py
"""

import time

import requests

# API endpoint
API_URL = "http://localhost:8000/graphql"

# GraphQL queries and mutations


def health_check():
    """Check if the API is healthy and accessible."""
    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        print("✓ API is healthy:", response.json())
        return True
    print("✗ API health check failed")
    return False


def get_api_info():
    """Get API metadata information."""
    response = requests.get("http://localhost:8000/")
    if response.status_code == 200:
        info = response.json()
        print("\nAPI Information:")
        print(f"  Name: {info['name']}")
        print(f"  Version: {info['version']}")
        print(f"  GraphQL Endpoint: {info['graphql_endpoint']}")
        return info
    return None


def start_scan(directory: str = "/app/videos", scan_mode: str = "QUICK"):
    """Start a new video scan via GraphQL mutation."""
    mutation = """
    mutation StartScan($directory: String!, $scanMode: ScanModeType!) {
        startScan(input: {
            directory: $directory
            scanMode: $scanMode
            recursive: true
            resume: true
        }) {
            id
            directory
            scanMode
            status
            startedAt
            resultsCount
        }
    }
    """

    variables = {"directory": directory, "scanMode": scan_mode}

    response = requests.post(API_URL, json={"query": mutation, "variables": variables})

    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("✗ GraphQL errors:", data["errors"])
            return None

        scan_job = data["data"]["startScan"]
        print("\n✓ Scan started successfully!")
        print(f"  Job ID: {scan_job['id']}")
        print(f"  Directory: {scan_job['directory']}")
        print(f"  Mode: {scan_job['scanMode']}")
        print(f"  Status: {scan_job['status']}")
        return scan_job
    print(f"✗ Request failed with status {response.status_code}")
    return None


def get_all_scan_jobs():
    """Query all scan jobs via GraphQL."""
    query = """
    query GetScanJobs {
        scanJobs {
            id
            directory
            scanMode
            status
            startedAt
            completedAt
            resultsCount
        }
    }
    """

    response = requests.post(API_URL, json={"query": query})

    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("✗ GraphQL errors:", data["errors"])
            return []

        jobs = data["data"]["scanJobs"]
        print(f"\n✓ Found {len(jobs)} scan job(s):")
        for job in jobs:
            print(f"  - ID: {job['id']}")
            print(f"    Directory: {job['directory']}")
            print(f"    Status: {job['status']}")
            print(f"    Results: {job['resultsCount']}")
        return jobs
    print(f"✗ Request failed with status {response.status_code}")
    return []


def get_scan_summary(job_id: str):
    """Get summary for a specific scan job."""
    query = """
    query GetScanSummary($jobId: String!) {
        scanSummary(jobId: $jobId) {
            directory
            totalFiles
            processedFiles
            corruptFiles
            healthyFiles
            scanMode
            scanTimeSeconds
            successRate
            filesPerSecond
        }
    }
    """

    variables = {"jobId": job_id}

    response = requests.post(API_URL, json={"query": query, "variables": variables})

    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("✗ GraphQL errors:", data["errors"])
            return None

        summary = data["data"]["scanSummary"]
        if summary:
            print(f"\n✓ Scan Summary for job {job_id}:")
            print(f"  Total Files: {summary['totalFiles']}")
            print(f"  Processed: {summary['processedFiles']}")
            print(f"  Corrupt: {summary['corruptFiles']}")
            print(f"  Healthy: {summary['healthyFiles']}")
            print(f"  Scan Time: {summary['scanTimeSeconds']:.2f}s")
            print(f"  Success Rate: {summary['successRate']:.1f}%")
            return summary
        print(f"✗ No summary found for job {job_id}")
        return None
    print(f"✗ Request failed with status {response.status_code}")
    return None


def generate_report(job_id: str, format: str = "json"):
    """Generate a report for a completed scan."""
    mutation = """
    mutation GenerateReport($jobId: String!, $format: String!) {
        generateReport(input: {
            scanJobId: $jobId
            format: $format
            includeHealthy: false
            prettyPrint: true
        }) {
            id
            format
            filePath
            createdAt
            scanSummary {
                totalFiles
                corruptFiles
            }
        }
    }
    """

    variables = {"jobId": job_id, "format": format}

    response = requests.post(API_URL, json={"query": mutation, "variables": variables})

    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("✗ GraphQL errors:", data["errors"])
            return None

        report = data["data"]["generateReport"]
        if report:
            print("\n✓ Report generated successfully!")
            print(f"  Report ID: {report['id']}")
            print(f"  Format: {report['format']}")
            print(f"  File Path: {report['filePath']}")
            return report
        print("✗ Failed to generate report")
        return None
    print(f"✗ Request failed with status {response.status_code}")
    return None


def main():
    """Main example workflow."""
    print("=" * 60)
    print("Corrupt Video Inspector - GraphQL API Example")
    print("=" * 60)

    # Step 1: Health check
    if not health_check():
        print("\nError: API is not accessible. Make sure it's running:")
        print("  make run-api")
        print("  # or")
        print("  docker compose --profile api up")
        return

    # Step 2: Get API info
    get_api_info()

    # Step 3: Start a scan
    print("\n" + "-" * 60)
    print("Starting a new scan...")
    print("-" * 60)
    scan_job = start_scan(directory="/app/videos", scan_mode="QUICK")

    if not scan_job:
        print("Failed to start scan. Check the logs.")
        return

    job_id = scan_job["id"]

    # Step 4: Wait a moment for the scan to complete
    # In a real application, you might poll the status or use webhooks
    print("\nWaiting for scan to complete...")
    time.sleep(2)

    # Step 5: Get all scan jobs
    print("\n" + "-" * 60)
    print("Retrieving all scan jobs...")
    print("-" * 60)
    get_all_scan_jobs()

    # Step 6: Get scan summary
    print("\n" + "-" * 60)
    print("Retrieving scan summary...")
    print("-" * 60)
    get_scan_summary(job_id)

    # Step 7: Generate a report
    print("\n" + "-" * 60)
    print("Generating report...")
    print("-" * 60)
    generate_report(job_id, format="json")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
