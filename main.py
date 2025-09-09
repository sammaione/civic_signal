from dotenv import load_dotenv
load_dotenv()  # reads .env into the process environment for terminal runs

import os, sys, requests
import json
from datetime import datetime, timezone

API_KEY = os.getenv("CONGRESS_API_KEY")
if not API_KEY:
    sys.exit("Missing CONGRESS_API_KEY. Create .env from .env.example and set your key.")

def get_bill_text(congress: int, chamber: str, number: int) -> list:
    url = f"https://api.congress.gov/v3/bill/{congress}/{chamber}/{number}/text?format=json"
    response = requests.get(url, headers={"X-Api-Key": API_KEY}, timeout=20)
    response.raise_for_status()
    return response.json()["textVersions"]

def find_latest_URL(bill_status_dates: list):
    d = {}
    for index, entry in enumerate(bill_status_dates):
        d.update({f"{entry["date"]}": index})
    sorted_d = dict(sorted((k, v) for k, v in d.items() if k != "None"))
    value_list = list(sorted_d.values())
    return bill_status_dates[value_list[-1]]["formats"]

if __name__ == "__main__":
    print("Fetching OBBB metadata…")
    bill_text_metadata = get_bill_text(119, "hr", 1)
    bill_latest_dated_version = find_latest_URL(bill_text_metadata)
    pretty_json = json.dumps(bill_latest_dated_version, indent=4)
    print(pretty_json)