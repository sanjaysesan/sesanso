import argparse
import json
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def search(keywords, location, days):
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": os.environ.get("ADZUNA_APP_ID", ""),
        "app_key": os.environ.get("ADZUNA_APP_KEY", ""),
        "what": keywords,
        "where": location,
        "max_days_old": days,
        "results_per_page": 20,
        "sort_by": "date",
        "content-type": "application/json",
    }

    if not params["app_id"] or not params["app_key"]:
        raise RuntimeError("ADZUNA_APP_ID or ADZUNA_APP_KEY missing in .env file.")

    resp = requests.get(url, params=params, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(f"Job feed returned HTTP {resp.status_code}")

    seen, jobs = set(), []
    for r in resp.json().get("results", []):
        key = (r["title"].lower(), r["company"]["display_name"].lower())
        if key in seen:
            continue
        seen.add(key)
        jobs.append({
            "source": "Multi-Board Aggregator (LinkedIn/Naukri/Indeed/Career Pages)",
            "title": r.get("title"),
            "company": r.get("company", {}).get("display_name", "Unknown"),
            "location": r.get("location", {}).get("display_name", location),
            "posted": r.get("created"),
            "url": r.get("redirect_url"),
            "description": r.get("description", ""),
        })
    return jobs

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Search multi-board jobs")
    p.add_argument("--keywords", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--days", type=int, default=7, help="Days old")
    args = p.parse_args()

    try:
        jobs = search_jobs(args.keywords, args.location, args.days)
    except Exception as e:
        print(json.dumps({"error": str(e), "jobs": []}))
        sys.exit(1)

    print(json.dumps({"count": len(jobs), "jobs": jobs}, indent=2))