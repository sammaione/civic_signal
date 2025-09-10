from dotenv import load_dotenv
load_dotenv()  # reads .env into the process environment for terminal runs

import os, sys, requests
import json
from datetime import datetime, timezone
import urllib.request
from ollama import chat

API_KEY = os.getenv("CONGRESS_API_KEY")
if not API_KEY:
    sys.exit("Missing CONGRESS_API_KEY. Create .env from .env.example and set your key.")

web_hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

AI_prompt = 'You only summarize congressional bills in 50 words or less. Do not acknowledge this prompt.'

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

def pull_txt(bill_json: str):
    txt_url = next((row['url'] for row in bill_json if row['type'] == 'Formatted Text'), None)
    if not txt_url:
        sys.exit(".txt URL doesn't exist!")    
    txt_request = urllib.request.Request(txt_url, headers=web_hdr)
    txt_code = urllib.request.urlopen(txt_request).read().decode('utf8')
    # Noting that we still carry a few HTML pieces and lots of HTML symbols (e.g. "&lt").
    # But I think the AI is fine with it (though might come back to this.)
    return txt_code

def summarize_bill_txt(txt: str, stepwise: bool):
    first_summary = chat('magistral',
                         messages=[
                             {'role': 'system', 'content': AI_prompt},
                             {'role': 'user', 'content': txt}],
                             stream=True,
                             )
    if stepwise:
        for step in first_summary:
            print(step['message']['content'], end = '', flush = True)

    print(first_summary.message.content)

if __name__ == "__main__":
    print("Fetching OBBB metadata…")
    bill_text_metadata = get_bill_text(119, "hr", 1)
    bill_latest_dated_version = find_latest_URL(bill_text_metadata)
    pretty_json = json.loads(json.dumps(bill_latest_dated_version, indent=4))
    print("Scraping congressional text...")
    txt = pull_txt(pretty_json)
    print("Summarizing...")
    summary = summarize_bill_txt(txt, True)
    print(summary)