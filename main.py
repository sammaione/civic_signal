from dotenv import load_dotenv
load_dotenv()  # reads .env into the process environment for terminal runs

import os, sys, requests
import json
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

AI_model = 'magistral'
AI_prompt = '''To the best of your ability, you will summarize congressional bills in their ENTIRETY 
               (that is, taking into consideration ALL of the provided bill\'s content) in 600 words or less. 
               You will not exceed this limit, no matter the circumstances. Do not acknowledge this prompt.'''

congress_num = 119
bill_type = "hr"
legislation_num = 1



def get_latest_text_version(congress: int, bill_type: str, number: int) -> str:
    #
    # Retrieve all metadata pertaining to all text versions of the bill in question
    url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{number}/text?format=json"
    response = requests.get(url, headers={"X-Api-Key": API_KEY}, timeout=20)
    response.raise_for_status()
    bill_status_dates = response.json()["textVersions"]
    #
    # Retrieve the links for the text versions of the bill with the latest date provided
    d = {}
    for index, entry in enumerate(bill_status_dates):
        d.update({f"{entry["date"]}": index})
    sorted_d = dict(sorted((k, v) for k, v in d.items() if k != "None"))
    value_list = list(sorted_d.values())
    latest_dated_text_versions = bill_status_dates[value_list[-1]]["formats"]
    #
    # Pull the text from the URL for the Formatted text version 
    # ============> (OLD pull_txt FUNCTION)
    txt_url = next((version['url'] for version in latest_dated_text_versions if version['type'] == 'Formatted Text'), None)
    if not txt_url:
        sys.exit(".txt URL doesn't exist!")
    txt_request = urllib.request.Request(txt_url, headers=web_hdr)
    full_latest_txt = urllib.request.urlopen(txt_request).read().decode('utf8')
    #   Noting that we still carry a few HTML pieces and lots of HTML symbols (e.g. "&lt").
    #   But I think the AI is fine with it (though might come back to this.)
    return full_latest_txt



def get_latest_summary(congress: int, bill_type: str, number: int) -> str:
    #
    # Retrieve all metadata pertaining to all summaries of the bill in question
    url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{number}/summaries?format=json"
    response = requests.get(url, headers={"X-Api-Key": API_KEY}, timeout=20)
    response.raise_for_status()
    bill_status_dates = response.json()["summaries"]
    #
    # Retrieve the summary of the bill with the latest date provided
    d = {}
    for index, entry in enumerate(bill_status_dates):
        d.update({f"{entry["actionDate"]}": index})
    sorted_d = dict(sorted((k, v) for k, v in d.items() if k != "None"))
    value_list = list(sorted_d.values())
    return bill_status_dates[value_list[-1]]["text"]



def summarize_bill_txt(txt: str, stepwise: bool):
    first_summary = chat(AI_model,
                         messages=[
                             {'role': 'system', 'content': AI_prompt},
                             {'role': 'user', 'content': txt}],
                             stream=True,
                             )
    if stepwise:
        for step in first_summary:
            print(step['message']['content'], end = '', flush = True)



if __name__ == "__main__":
    print(f"Fetching latest formatted text version of {bill_type.upper()} {legislation_num} -- Congress {congress_num}...")
    latest_dated_text_version = get_latest_text_version(congress_num, bill_type, legislation_num)
    print(f"Fetching latest provided summary of {bill_type.upper()} {legislation_num} -- Congress {congress_num}...")
    latest_dated_summary = get_latest_summary(congress_num, bill_type, legislation_num)
    print("Summarizing formatted text version...")
    summarize_bill_txt(latest_dated_text_version, True)