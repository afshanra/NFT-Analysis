
import imagehash
from skimage.metrics import structural_similarity as ssim
from utils import *
from processing import *
from PIL import Image
import logging
import pandas as pd
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

def compare_images(opensea_image, original_image, asset_id, results_path, opensea_extension, original_extension):

    try:
        # Convert images to grayscale for SSIM computation
        opensea_grey = np.array(opensea_image.convert('L'))
        original_grey = np.array(original_image.convert('L'))

        # Compute SSIM between two images
        ssim_score = ssim(opensea_grey,original_grey)
        
        # Compute Mean Square Error between two images
        if opensea_image.size != original_image.size:
            raise ValueError("Images must be the same size for MSE calculation")
        mse_score = np.mean((opensea_grey -original_grey) ** 2)
        
        # Compute pHash for both images
        opensea_phash = imagehash.phash(opensea_image, hash_size=16)
        original_phash = imagehash.phash(original_image, hash_size=16)
        phash_diff = opensea_phash - original_phash

        # Save the results to a CSV file
        results = {
            'asset_id': asset_id,
            'ssim_score': ssim_score,
            'mse_score' : mse_score,
            #'opensea_phash': str(opensea_phash),
            #'original_phash': str(original_phash),
            'phash_difference': phash_diff,
            'opensea_extension': opensea_extension,
            'original_extension': original_extension
        }
        df_results = pd.DataFrame([results])
        df_results.to_csv(results_path, mode='a', header=not pd.io.common.file_exists(results_path), index=False)

        logger.info(f"Comparison for asset ID {asset_id} saved to {results_path}")
    except Exception as e:
        logger.error(f"Error comparing images for asset ID {asset_id}: {e}")

