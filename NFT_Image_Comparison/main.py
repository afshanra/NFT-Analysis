
import pandas as pd
from processing import *
from comparison import *
from utils import *
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time


# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to lowest level to capture all logs

# Create a console handler and set level to DEBUG
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter and set it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s:%(name)s: %(message)s')
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)

# Path to the CSV files
csv_path = "missed_november.csv"
results_csv_path = "/data/comparison_results.csv"
error_log_path = "/data/error_log.csv"


# Initialize sets for processed IDs and errors logged
processed_ids = set()
errors_logged = set()

# Locks for thread safety
processed_ids_lock = threading.Lock()
errors_logged_lock = threading.Lock()


def process_row(row, processed_ids, errors_logged, processed_ids_lock, errors_logged_lock):
    asset_id = row.get('asset_id')

    with processed_ids_lock:
        if asset_id in processed_ids:
            logger.info(f"Asset ID {asset_id} has already been processed.")
            return None

    try:
        result = download_and_process_image(row, errors_logged)
        if result['opensea_image'] and result['original_image']:
            # Compare images and write results
            compare_images(result['opensea_image'], result['original_image'], asset_id, results_csv_path, result['opensea_extension'], result['original_extension'])
            with processed_ids_lock:
                processed_ids.add(asset_id)
        return asset_id
    except Exception as e:
        logger.error(f"Error processing asset ID {asset_id}: {e}")
        with errors_logged_lock:  # Acquire lock before modifying errors_logged
            errors_logged.add(asset_id)
        with processed_ids_lock:
            processed_ids.add(asset_id)
        return None


def process_batch(df_batch, processed_ids, errors_logged):
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_row = {executor.submit(process_row, row, processed_ids, errors_logged, processed_ids_lock, errors_logged_lock): row for _, row in df_batch.iterrows()}

        for future in as_completed(future_to_row):
            future.result()
def initialize_processed_and_error_sets(processed_ids, errors_logged, results_csv_path, error_log_path):
    # Read asset_ids from comparison_results.csv
    try:
        comparison_results = pd.read_csv(results_csv_path)
        for asset_id in comparison_results['asset_id']:
            processed_ids.add(asset_id)
    except FileNotFoundError:
        logger.info(f"No existing comparison results found at {results_csv_path}")

    # Read asset_ids from error_log.csv
    try:
        error_log = pd.read_csv(error_log_path)
        for asset_id in error_log['asset_id']:
            errors_logged.add(asset_id)
    except FileNotFoundError:
        logger.info(f"No existing error log found at {error_log_path}")

def main():
    # Initialize sets with existing processed IDs and errors
    initialize_processed_and_error_sets(processed_ids, errors_logged, results_csv_path, error_log_path)

    chunk_size = 10000
    for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
        process_batch(chunk, processed_ids, errors_logged)
        time.sleep(60)

if __name__ == "__main__":
    main()

