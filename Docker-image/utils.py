#utils.py
import requests
from PIL import Image, ImageOps
from io import BytesIO
import cairosvg
import logging
import pandas as pd
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_error_to_csv(error_data, error_log_path):
    df_error = pd.DataFrame([error_data])
    df_error.to_csv(error_log_path, mode='a', header=not pd.io.common.file_exists(error_log_path), index=False)
    
    
def svg_to_png(svg_content):
    try:
        png_image = cairosvg.svg2png(bytestring=svg_content)
        return Image.open(BytesIO(png_image))
    except Exception as e:
        logger.error("Error converting SVG to PNG: %s", e)
        raise

def add_background(pil_img, color=(76, 105, 113)):
    if pil_img.mode == 'P' and 'transparency' in pil_img.info:
        pil_img = pil_img.convert('RGBA')
    elif pil_img.mode != 'RGBA':
        raise ValueError("Image does not have an alpha channel.")
    background = Image.new("RGB", pil_img.size, color)
    background.paste(pil_img, mask=pil_img.split()[3])
    return background

def get_extension(content_type):
    if 'image' in content_type:
        return content_type.split('/')[-1]  # Split and return the extension part
    else:
        logger.warning(f"Content-Type is not recognized as an image {asset_id}: {content_type}")
        return 'unknown' 

# Modify IPFS URL to a downloadable link
def modify_ipfs_url(url):
    if url.startswith('ipfs://'):
        return url.replace('ipfs://', 'http://ipfs:8080/ipfs/')
    elif 'https://ipfs.tech/' in url:
        return url.replace('https://ipfs.tech/', 'http://ipfs:8080/ipfs/')
    elif '/ipfs/' in url:
        return 'http://ipfs:8080/ipfs/' + url.split('/ipfs/')[1]     
    return url  


def process_image(image, row, errors_logged, size=(256, 256), error_log_path='error_log.csv'):
    asset_id = row.get('asset_id')

    try:
        if image.mode == 'RGBA':
            image = add_background(image)
        image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
        return image

    except ValueError as e:
        if asset_id not in errors_logged:  # Check if asset ID error is already logged
            logger.error(f"Invalid image format for {asset_id}: {e}")
            error_data = row.to_dict()
            error_data['error_type'] = 'format error'
            log_error_to_csv(error_data, error_log_path)
            errors_logged.add(asset_id)

    except Exception as e:
        if asset_id not in errors_logged:  # Check if asset ID error is already logged
            error_message = f"Error processing {asset_id}: {e}"
            logger.error(error_message)
            error_data = row.to_dict()
            error_data['error_type'] = 'processing error'
            log_error_to_csv(error_data, error_log_path)
            errors_logged.add(asset_id)

def process_json(json_data, original_url, row, error_log_path):
    
    # Adjust this based on the actual structure of your JSON files
    if 'image' in json_data:
        # Process the image URL found in the JSON
        image_url = json_data['image']
        processed_image, _ = download_image(image_url, row)
        if processed_image:
            # Replace the image URL in the JSON with the original URL
            json_data['image'] = original_url
    return json_data


def download_image(url, row, errors_logged, timeout=60, error_log_path='error_log.csv'):
    asset_id = row.get('asset_id')

    # Ensure errors_logged is a set
    if not isinstance(errors_logged, set):
        errors_logged = set()

    if asset_id in errors_logged:
        # Skip processing if this asset ID has already been logged
        return None, None

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        time.sleep(0.01)  # Delay after each request

        # Check if the content is JSON
        if 'application/json' in response.headers['Content-Type']:
            return process_json(response.json(), url, row, error_log_path), response.headers['Content-Type']
        
        # Check if the content is SVG and convert it if necessary
        if 'image/svg+xml' in response.headers['Content-Type']:
            image = svg_to_png(response.content)
        else:
            image = Image.open(BytesIO(response.content))

        # Return both the image and the content type
        return image, response.headers['Content-Type']

    except Exception as e:
        error_message = f"Error downloading image asset ID: {asset_id} : {url}: {e}"
        if asset_id not in errors_logged:
            logger.error(error_message)
            error_data = row.to_dict()
            error_data['error_type'] = 'download error'
            log_error_to_csv(error_data, error_log_path)
            errors_logged.add(asset_id)

        return None, None



