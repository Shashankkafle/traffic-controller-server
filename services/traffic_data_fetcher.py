import json
import pandas as pd
import requests
import os
from dotenv import load_dotenv

def parse_traffic_api_data(data_point):
    # Extract headers
    headers = data_point["raw"]["data"]["header"]
    print("Headers:", headers)
    print("payload_name:", data_point["payload_name"])

    # Extract rows
    rows = data_point["raw"]["data"]["data"]

    print(rows)

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=headers)
    pd.set_option("display.max_columns", None)

    return df

def fetch_traffic_data(params):
    response = requests.get(os.environ.get("TRAFFIC_DATA_API"))
    print("Status code:", response)
    response_data = response.json()
    print(response.json()['data'][0]['raw']['data']['data'])
    print("response data:", response_data)
