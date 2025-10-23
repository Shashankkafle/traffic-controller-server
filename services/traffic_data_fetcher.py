import json
import requests
import os
import uuid
# payloads_to_observe = [
#     "Way_IN_Table - Table",
#     "Traffic_Zone_Dashboard - Table",
#      "Way_Out_Table - Table"
# ]
def parse_traffic_api_data(api_response):
    """
    Convert nested traffic data with headers into a list of dictionaries.
    
    Args:
        data_block (dict): The dictionary containing 'header' and 'data' keys.
        
    Returns:
        list[dict]: A list of dictionaries mapping header names to data values.

    """
    push = False
    temp_stack = []

    result = []
    for block in api_response.get("data", []):
        payload_name = block.get("payload_name")
        if not payload_name or not payload_name.endswith("Table"):
            continue
        rows = block["data"]["data"]["data"]
        header = block["data"]["data"]["header"]

        push = not push
        for row in rows:
            # zip headers to corresponding values and convert to dict
            entry = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
            entry["payload_name"] = payload_name
            # mocking  lisense plate for now
            if push:
                license_plate = str(uuid.uuid4())
                entry["License plate"] = license_plate
                temp_stack.append(license_plate)
            else:
                license_plate = temp_stack.pop() if temp_stack else '-'
                entry["License plate"] = license_plate
            # mock logic ends here
            result.append(entry)
    return result



def fetch_traffic_data(params):
    # with open('services/dummy_response.json', 'r', encoding='utf-8') as file:
    #     response = json.load(file)
    response = requests.get("http://85.204.247.82:3030/api/datafromsky/")
    df = parse_traffic_api_data(response.json())
    return df