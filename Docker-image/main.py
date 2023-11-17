
import pandas as pd
from processing import download_and_process_image
from comparison import compare_images
from utils import *
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time


# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to lowest level to capture all logs

# Create a file handler and set level to DEBUG
file_handler = logging.FileHandler('output_log.txt')
file_handler.setLevel(logging.DEBUG)  # Capture all types of logs in the file

# Create a console handler and set level to DEBUG
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter and set it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s:%(name)s: %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Path to the CSV file and output files
csv_path = "clean_nft_dataset.csv"
results_csv_path = "/data/comparison_results.csv"
error_log_path = "/data/error_log.csv"

# Initialize sets for processed IDs and errors logged
processed_ids = set()
errors_logged = set()

# Locks for thread safety
processed_ids_lock = threading.Lock()
errors_logged_lock = threading.Lock()

def process_row(row, processed_ids, errors_logged, processed_ids_lock, errors_logged_lock):
    with processed_ids_lock:
        asset_id = row.get('asset_id')
        if asset_id in processed_ids:
            logger.info(f"Asset ID {asset_id} has already been processed.")
            return None

    try:
        result = download_and_process_image(row, errors_logged)
        if result['opensea_image'] and result['original_image']:
            # Compare images and write results
            compare_images(result['opensea_image'], result['original_image'], asset_id, results_csv_path)
            with processed_ids_lock:
                processed_ids.add(asset_id)
            return asset_id
    except Exception as e:
        logger.error(f"Error processing asset ID {asset_id}: {e}")
        with processed_ids_lock:
            processed_ids.add(asset_id)
        return None

def process_batch(df_batch, processed_ids, errors_logged):
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_row = {executor.submit(process_row, row, processed_ids, errors_logged, processed_ids_lock, errors_logged_lock): row for _, row in df_batch.iterrows()}

        for future in as_completed(future_to_row):
            future.result()

def main():
	
    chunk_size = 1000

    for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
        process_batch(chunk, processed_ids, errors_logged)
        time.sleep(60)
	
if __name__ == "__main__":
    main()
