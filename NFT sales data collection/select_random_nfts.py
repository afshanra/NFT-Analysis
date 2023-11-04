import argparse
import csv
import requests
import time
from datetime import datetime, timedelta
from requests.exceptions import Timeout, RequestException

try:
    import api_key
except ImportError:
    print("Unable to find ./api_key.py")
    exit(1)

if not api_key.OPENSEA_APIKEY:
    print("OPENSEA_APIKEY is empty")
    exit(1)

# Define the OpenSea API endpoint
OPENSEA_API_ENDPOINT = "https://api.opensea.io/api/v1/events"

# Define the function to get events from OpenSea API
def get_events(start_datetime, end_datetime, cursor="", event_type="successful", limit=300):
    headers = {
        "Accept": "application/json",
        "X-API-KEY": api_key.OPENSEA_APIKEY
    }

    params = {
        "only_opensea": "false",
        "event_type": event_type,
        "occurred_after": start_datetime.isoformat(),
        "occurred_before": end_datetime.isoformat(),
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
    parser.add_argument('-s', "--start_datetime", required=True, help="Start date and time in ISO8601 format")
    parser.add_argument('-e', "--end_datetime", required=True, help="End date and time in ISO8601 format")
    args = parser.parse_args()

    start_datetime = datetime.fromisoformat(args.start_datetime)
    end_datetime = datetime.fromisoformat(args.end_datetime)

    csv_filename = "nft.csv"

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

        current_datetime = start_datetime
        total_items_written = 0

        while current_datetime <= end_datetime:
            total_items_written_timeframe = 0  # Total items written for the current time frame

            current_minute = 0

            while current_minute < 60:
                start_time = current_datetime.replace(minute=current_minute)
                end_time = start_time + timedelta(minutes=120)

                print(f"Chosen time frame: {start_time} to {end_time}")

                cursor = None

                while True:
                    try:
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
                        print(f"An error occurred: {str(e)}")
                        continue

                print(f"Data collected for {current_datetime.date()} {start_time.time()}: {total_items_written} items")

                current_minute += 120

            current_datetime += timedelta(hours=2)

if __name__ == "__main__":
    main()

