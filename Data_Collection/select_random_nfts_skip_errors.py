import argparse
import csv
import requests
import time
import random
from datetime import datetime, timedelta
from requests.exceptions import Timeout, RequestException

try:
    import config
except ImportError:
    print("Unable to find ./config.py. Please see the instructions in README.md")
    exit(1)

if not config.OPENSEA_APIKEY:
    print("OPENSEA_APIKEY is empty in config.py")
    exit(1)

# Define the OpenSea API endpoint
OPENSEA_API_ENDPOINT = "https://api.opensea.io/api/v1/events"

# Define the function to get events from OpenSea API
def get_events(start_datetime, end_datetime, cursor="", event_type="successful", limit=300):
    headers = {
        "Accept": "application/json",
        "X-API-KEY": config.OPENSEA_APIKEY
    }

    params = {
        "only_opensea": "false",
        "event_type": event_type,
        "occurred_after": int(start_datetime.timestamp()),
        "occurred_before": int(end_datetime.timestamp()),
        "limit": limit,
        "cursor": cursor
    }

    try:
        response = requests.get(OPENSEA_API_ENDPOINT, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except Timeout:
        print("Request timed out. Retrying...")
        return get_events(start_datetime, end_datetime, cursor, event_type, limit)
    except RequestException as e:
        print(f"Request error: {str(e)}")
        return None

# Define the function to parse the event data
def parse_event(event):
    asset = event.get('asset')
    if asset is None:
        return None  # If there's no asset, it's not a single NFT transaction, so skip this item

    # Extract the required parameters
    record = {
        'asset_id': asset['id'],
        'asset_name': asset['name'],
        'asset_token_id': asset['token_id'],
        'asset_contract_date': asset['asset_contract']['created_date'],
        'asset_contract_address': asset['asset_contract']['address'],
        'chain_identifier': asset['asset_contract']['chain_identifier'],
        'asset_contract_type': asset['asset_contract']['asset_contract_type'],
        'owner': asset['asset_contract']['owner'],
        'schema_name': asset['asset_contract']['schema_name'],
        'symbol': asset['asset_contract']['symbol'],
        'external_link': asset['external_link'],
        'asset_url': asset['permalink'],
        'asset_img_url': asset['image_url'],
        'animation_url': asset['animation_url'],
        'asset_img_org_url': asset['image_original_url'],
        'animation_org_url': asset['animation_original_url'],
    }

    # Extract the collection parameters
    collection = asset.get('collection', {})
    record['collection_slug'] = collection.get('slug', "")
    record['collection_name'] = collection.get('name', "")
    record['collection_url'] = f"https://opensea.io/collection/{record['collection_slug']}"
    record['collection_created_date'] = collection.get('created_date', "")
    record['featured'] = collection.get('featured', "")
    record['featured_image_url'] = collection.get('featured_image_url', "")
    record['safelist_request_status'] = collection.get('safelist_request_status', "")
    record['is_nsfw'] = collection.get('is_nsfw', "")
    record['hidden'] = collection.get('hidden', "")
    record['seller_fee'] = collection.get('fees', {}).get('seller_fees', "")
    record['token_metadata'] = asset.get('token_metadata', "")
    record['collection_discord_url'] = collection.get('discord_url', "")

    # Extract event parameters
    record['event_id'] = event.get('id', "")
    record['event_time'] = event.get('created_date', "")
    record['event_contract_address'] = event.get('contract_address', "")

    return record

# Define the main function to retrieve and save event data
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', "--start_date", required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument('-e',"--end_date", required=True, help="End date in YYYY-MM-DD format")
    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d %H:%M")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d %H:%M")

    csv_filename = "Apr2022.csv"

    with open(csv_filename, mode="w", encoding="utf-8", newline="\n") as csv_file:
        fieldnames = [
            'asset_id', 'asset_name', 'asset_token_id', 'asset_contract_date',
            'asset_contract_address', 'chain_identifier', 'asset_contract_type',
            'owner', 'schema_name', 'symbol', 'external_link',
            'asset_url', 'asset_img_url', 'animation_url', 'asset_img_org_url',
            'animation_org_url', 'collection_slug', 'collection_name', 'collection_url',
            'collection_created_date', 'featured', 'featured_image_url',
            'safelist_request_status', 'is_nsfw', 'hidden', 'seller_fee',
            'token_metadata', 'collection_discord_url', 'event_id', 'event_time',
            'event_contract_address'
        ]

        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        while start_date <= end_date:
            total_items_written = 0
            current_hour = 0

            while current_hour < 24:
                current_minute = 0

                while current_minute < 60:
                    start_time = start_date.replace(hour=current_hour, minute=current_minute)
                    end_time = start_time + timedelta(minutes=60)

                    print(f"Chosen time frame for {start_date.date()}: {start_time.time()} to {end_time.time()}")

                    cursor = None

                    try:
                        while True:
                            event_data = get_events(start_time, end_time, cursor=cursor)

                            if event_data:
                                for event in event_data.get("asset_events", []):
                                    record = parse_event(event)
                                    if record:
                                        writer.writerow(record)
                                        total_items_written += 1

                            cursor = event_data.get("cursor")
                            if not cursor:
                                break

                            time.sleep(3)

                    except Exception as e:
                        print(f"Error: {str(e)}")
                        pass  # Skip this time frame and continue to the next

                    print(f"Data collected for {start_date.date()} {start_time.time()}: {total_items_written} items")

                    current_minute += 60

                current_hour += 1

            start_date = start_date + timedelta(days=1)

if __name__ == "__main__":
    main()

