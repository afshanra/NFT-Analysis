import argparse
import csv
from datetime import datetime, timezone
import requests
import sys
from time import sleep

try:
    import api_key
except:
    sys.exit('Unable to find ./api_key.py. Please see the instruction in README.md')

if (api_key.OPENSEA_APIKEY == ''):
    sys.exit('OPENSEA_APIKEY is empty in api_key.py')


def get_events(start_date, end_date, cursor='', event_type='successful', **kwargs):
    url = "https://api.opensea.io/api/v1/events"
    query = {"only_opensea": "false",
             "occurred_before": end_date,
             "occurred_after": start_date,
             "event_type": event_type,
             "cursor": cursor,
             **kwargs
             }

    headers = {
        "Accept": "application/json",
        "X-API-KEY": api_key.OPENSEA_APIKEY
    }
    response = requests.request("GET", url, headers=headers, params=query)

    return response.json()
# Define the function to parse the event data
def parse_event(event):
    record = {}
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


def fetch_all_events(start_date, end_date, pause=1, **kwargs):
    result = list()
    next = ''
    fetch = True

    print(f"Fetching events between {start_date} and {end_date}")
    while fetch:
        response = get_events(int(start_date.timestamp()), int(end_date.timestamp()), cursor=next, **kwargs)

        # Check if 'asset_events' key is present in the response
        if 'asset_events' in response:
            for event in response['asset_events']:
                cleaned_event = parse_event(event)
                if cleaned_event is not None:
                    result.append(cleaned_event)

            if response['next'] is None:
                fetch = False
            else:
                next = response['next']
        else:
            # Print the response to debug the issue
            print("Unexpected response format:")
            print(response)
            fetch = False  # Exit the loop since there's an issue with the API response

        sleep(pause)

    return result


def write_csv(data, filename):
    with open(filename, mode='w', encoding='utf-8', newline='\n') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())

        writer.writeheader()
        for event in data:
            writer.writerow(event)


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)


def valid_datetime(arg_datetime_str):
    try:
        return datetime.strptime(arg_datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            return datetime.strptime(arg_datetime_str, "%Y-%m-%d")
        except ValueError:
            msg = "Given Datetime ({0}) not valid! Expected format, 'YYYY-MM-DD' or 'YYYY-MM-DD HH:mm'!".format(
                arg_datetime_str)
            raise argparse.ArgumentTypeError(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', "--startdate", help="The Start Date (YYYY-MM-DD or YYYY-MM-DD HH:mm)", required=True,
                        type=valid_datetime)
    parser.add_argument('-e', "--enddate", help="The End Date (YYYY-MM-DD or YYYY-MM-DD HH:mm)", required=True,
                        type=valid_datetime)
    parser.add_argument('-p', '--pause', help='Seconds to wait between http requests. Default: 1', required=False,
                        default=1, type=float)
    parser.add_argument('-o', '--outfile', help='Output file path for saving nft sales record in csv format',
                        required=False, default='./20november.csv', type=str)
    args = parser.parse_args()
    res = fetch_all_events(args.startdate.replace(tzinfo=timezone.utc), args.enddate.replace(tzinfo=timezone.utc),
                           args.pause)

    if len(res) != 0:
        write_csv(res, args.outfile)

    print("Done!")


if __name__ == "__main__":
    main()
