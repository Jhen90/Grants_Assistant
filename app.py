import json
import sys
from pathlib import Path

import requests


API_URL = "https://api.grants.gov/v1/api/search2"
BODY = {"keyword": "youth development", "oppStatuses": "posted|forecasted", "rows": 25}


def find_items(data):
    # Try several likely keys used by the API
    # Special-case Grants.gov v1 shape
    if isinstance(data, dict) and "oppHits" in data:
        return data["oppHits"]
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict) and "oppHits" in data["data"]:
        return data["data"]["oppHits"]
    for key in ("opportunities", "results", "data", "response", "opps"):
        if isinstance(data, dict) and key in data:
            val = data[key]
            # sometimes 'response' wraps another dict
            if isinstance(val, dict) and "opportunities" in val:
                return val["opportunities"]
            if isinstance(val, list):
                return val
    # Fallback: if top-level is a list
    if isinstance(data, list):
        return data
    return []


def extract_field(item, keys):
    for k in keys:
        if k in item and item[k]:
            return item[k]
    # Some nested structures
    for k in keys:
        parts = k.split(".")
        cur = item
        ok = True
        for p in parts:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                ok = False
                break
        if ok and cur:
            return cur
    return ""


def format_item(item):
    title = extract_field(item, [
        "opportunityTitle",
        "title",
        "OpportunityTitle",
        "opportunity.title",
    ])
    agency = extract_field(item, ["agency", "awardingAgency", "Agency"])
    deadline = extract_field(item, ["closeDate", "submissionCloseDate", "closeDateTime"])
    link = extract_field(item, ["applyURL", "applyUrl", "url", "opportunityURL", "applicationUrl"])
    if not link:
        # Construct a Grants.gov detail page using the numeric id when available
        oid = item.get("id") or item.get("oppId") or item.get("opportunityId")
        if oid:
            link = f"https://www.grants.gov/web/grants/view-opportunity.html?oppId={oid}"
    return title or "(no title)", agency or "(no agency)", deadline or "(no deadline)", link or ""


def main():
    print("Querying Grants.gov for 'youth development' opportunities...")
    try:
        r = requests.post(API_URL, json=BODY, timeout=30)
    except Exception as e:
        print("Request failed:", e)
        sys.exit(1)

    if r.status_code != 200:
        print(f"Grants.gov returned status {r.status_code}")
        try:
            print(r.text)
        except Exception:
            pass
        sys.exit(1)

    try:
        data = r.json()
    except Exception as e:
        print("Failed to parse JSON response:", e)
        print(r.text[:1000])
        sys.exit(1)

    # Save raw response for debugging
    try:
        Path("raw-response.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass

    # Print top-level keys to help understand response shape
    if isinstance(data, dict):
        print("Top-level keys:", list(data.keys()))
    else:
        print("Response is not a dict; type:", type(data))

    items = find_items(data)
    print(f"Found {len(items)} raw items in response.")

    out_lines = ["# Grant Report\n", "Results for keyword: youth development\n"]
    count = 0
    for it in items:
        title, agency, deadline, link = format_item(it)
        count += 1
        out_lines.append(f"## {count}. {title}\n")
        out_lines.append(f"- **Agency:** {agency}\n")
        out_lines.append(f"- **Deadline:** {deadline}\n")
        if link:
            out_lines.append(f"- **Apply:** {link}\n")
        out_lines.append("\n")

    out_path = Path("grant-report.md")
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote report to {out_path.resolve()}")


if __name__ == "__main__":
    main()
