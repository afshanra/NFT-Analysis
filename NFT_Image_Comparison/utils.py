#utils.py
import requests
from PIL import Image, ImageOps
from io import BytesIO
import cairosvg
import logging
import pandas as pd
import time
import base64
import logging
from urllib.parse import unquote
from requests.exceptions import ConnectionError, Timeout, HTTPError




error_log_path = "/data/error_log.csv"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_error_to_csv(error_data, error_log_path):
    df_error = pd.DataFrame([error_data])
    df_error.to_csv(error_log_path, mode='a', header=not pd.io.common.file_exists(error_log_path), index=False)
    
 
def svg_to_png(svg_data):
    try:
        # Ensure svg_data is a string for startswith checks
        if isinstance(svg_data, bytes):
            svg_data = svg_data.decode('utf-8')

        # Decoding different SVG data formats
        if svg_data.startswith('<?xml') or svg_data.startswith('<svg'):
            # Handle raw SVG XML strings
            pass  # svg_data is already in the correct format
        elif svg_data.startswith('data:image/svg+xml;utf8,'):
            # Handle SVG data URLs with UTF-8 encoding
            svg_data = unquote(svg_data.split(',', 1)[1])
        elif svg_data.startswith('data:image/svg+xml,'):
            # Handle SVG data URLs
            svg_data = unquote(svg_data.split(',', 1)[1])
        elif svg_data.startswith('data:image/svg+xml;base64,'):
            # Handle Base64 encoded SVG data URLs
            encoded_data = svg_data.split(',')[1]
            svg_data = base64.b64decode(encoded_data).decode('utf-8')
        else:
            logger.error(f"Unexpected SVG data format: {svg_data[:30]}...")
            return None

        # Convert SVG to PNG
        png_image = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
        return Image.open(BytesIO(png_image))

    except Exception as e:
        logger.error(f"Error converting SVG to PNG: {e}")
        return None


def process_image(image, row, errors_logged, size=(500, 500), transparency_gray_value=255, error_log_path=error_log_path):
    asset_id = row.get('asset_id')

    try:
        # Convert 'P' mode images to 'RGBA' to ensure consistency
        if image.mode == 'P' and 'transparency' in image.info:
            image = image.convert('RGBA')

        # Process RGBA images to replace transparent pixels with gray
        if image.mode == 'RGBA':
            r, g, b, a = image.split()
            grayscale = Image.merge('RGB', (r, g, b)).convert('L')
            mask = Image.eval(a, lambda x: 0 if x == 0 else 255)
            background = Image.new('L', image.size, transparency_gray_value)
            background.paste(grayscale, mask=mask)
            image = background

        # Resize the image to the desired size
        image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
        return image

    except ValueError as e:
        if asset_id not in errors_logged:  # Check if asset ID error is already logged
            logger.error(f"Invalid image format for {asset_id}: {e}")
            error_data = row.to_dict()
            error_data['error_type'] = f"Invalid image format for : {e}"
            log_error_to_csv(error_data, error_log_path)
            errors_logged.add(asset_id)

    except Exception as e:
        if asset_id not in errors_logged:  # Check if asset ID error is already logged
            error_message = f"Error processing {asset_id}: {e}"
            logger.error(error_message)
            error_data = row.to_dict()
            error_data['error_type'] = f"Error processing: {e}"
            log_error_to_csv(error_data, error_log_path)
            errors_logged.add(asset_id)

def get_extension(content_type):
    if '/' in content_type:
        return content_type.split('/')[-1]
    else:
        return content_type  # Assuming it's already an extension



# Modify IPFS URL to a downloadable link
def modify_ipfs_url(url):
    if url.startswith('ipfs://'):
        return url.replace('ipfs://', 'http://ipfs:8080/ipfs/')
    elif 'ipfs.io' in url:  
    	return url.replace('https://ipfs.io/ipfs/', 'http://ipfs:8080/ipfs/')
    elif 'https://ipfs.tech/' in url:
        return url.replace('https://ipfs.tech/', 'http://ipfs:8080/ipfs/')
    elif '/ipfs/' in url:
        return 'http://ipfs:8080/ipfs/' + url.split('/ipfs/')[1]     
    return url  



def process_json(json_data, original_url, row, error_log_path):
    
    
    if 'image' in json_data:
        # Process the image URL found in the JSON
        image_url = json_data['image']
        processed_image, _ = download_image(image_url, row)
        if processed_image:
            # Replace the image URL in the JSON with the original URL
            json_data['image'] = original_url
    return json_data



def download_image(url, row, errors_logged, timeout=60, error_log_path=error_log_path, retry=False, is_original_image=False):
    asset_id = row.get('asset_id')

    if not isinstance(errors_logged, set):
        errors_logged = set()

    if asset_id in errors_logged:
        return None, None

    retry_timeout = 20 if retry else timeout
    try:
        if url.startswith('<?xml') or url.startswith('<svg'):
            # Handle raw SVG XML strings
            image = svg_to_png(url)
            return image, 'image/png'
        elif url.startswith('data:image/svg+xml;utf8,') or url.startswith('data:image/svg+xml,') or url.startswith('data:image/svg+xml;base64,'):
            # Handle different SVG data URL formats
            image = svg_to_png(url)
            return image, 'image/png'
        elif url.startswith('data:image/'):
            # Handle other image data URLs (PNG, JPEG, etc.)
            content_type = url.split(';')[0].split('/')[1]
            encoded_data = url.split(',')[1]
            data = base64.b64decode(encoded_data)
            image = Image.open(BytesIO(data))
            return image, f'image/{content_type}'
        else:
            # Regular image URLs
            response = requests.get(url, timeout=retry_timeout)
            response.raise_for_status()
            time.sleep(0.01)  # Delay after each request

            if 'image/svg+xml' in response.headers['Content-Type']:
                image = svg_to_png(response.content)
                return image, 'image/svg+xml'
            else:
                image = Image.open(BytesIO(response.content))
                return image, response.headers['Content-Type']

    except Exception as e:
    
        if 'ipfs:8080' in url and not retry and is_original_image and isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout,requests.exceptions.HTTPError)):  
            logger.error(f"Error downloading image asset ID: {asset_id} : {url}: {e}")
            new_url = url.replace('http://ipfs:8080/ipfs/', 'https://ipfs.io/ipfs/')
            logger.warning(f"Retrying with public gateway for asset ID: {asset_id}")
            return download_image(new_url, row, errors_logged, timeout, error_log_path, retry=True)


        error_message = f"Error downloading image {asset_id} : {url}: {e}"
        if asset_id not in errors_logged:
            logger.error(error_message)
            error_data = row.to_dict()
            error_data['error_type'] = f"Error downloading image : {url}: {e}"
            log_error_to_csv(error_data, error_log_path)
            errors_logged.add(asset_id)

        return None, None

