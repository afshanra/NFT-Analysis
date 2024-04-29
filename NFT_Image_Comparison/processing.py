from utils import *
import logging
import pandas as pd

# Set up logging
logger = logging.getLogger(__name__)

def download_and_process_image(row, errors_logged, timeout=60):
    asset_id = row.get('asset_id')
    # Initialize the result dictionary
    result = {
        'opensea_image': None,
        'original_image': None,
        'asset_id': asset_id,
        'error_message': '',
        'opensea_extension': None,
        'original_extension': None
    }

    def log_error(message, add_to_errors=True):
        if add_to_errors:
            if asset_id not in errors_logged:
                errors_logged.add(asset_id)
                logger.error(message)
        else:
            logger.error(message)

    # Download and process the OpenSea image
    try:
        opensea_image_url = row['asset_img_url']
        opensea_image, opensea_content_type = download_image(opensea_image_url, row, errors_logged, timeout)  
        result['opensea_image'] = process_image(opensea_image, row, errors_logged)
        result['opensea_extension'] = get_extension(opensea_content_type)
    except Exception as e:
        error_message = f"Error downloading OpenSea image {asset_id}: {e}\n"
        result['error_message'] += error_message
        log_error(error_message)
    # Download and process the original image
    try:
        original_image_url = modify_ipfs_url(row['asset_img_org_url'])
        original_image, original_content_type = download_image(original_image_url, row, errors_logged, timeout, is_original_image=True)
        result['original_image'] = process_image(original_image, row, errors_logged)
        result['original_extension'] = get_extension(original_content_type)
    except Exception as e:
        error_message = f"Error downloading original image {asset_id}: {e}"
        log_error(error_message, add_to_errors=False)

    return result


