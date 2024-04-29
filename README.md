Overview
This project investigates how OpenSea presents NFT (Non-Fungible Token) images and metadata compared to the original blockchain sources. It aims to analyze the consistency and accuracy of NFT data provided by OpenSea through a comparison with blockchain data.

Data Collection
The data collection process involves fetching NFT images and metadata from OpenSea using the Event API. Two Python scripts (Daily collection, random Collection) are provided in the data_collection directory for this purpose. These scripts utilize an API key for accessing OpenSea's data.
The project utilizes the OpenSea API NFT Sales repository available at https://github.com/Checco9811/opensea-api-nft-sales. 

Image Comparison
In the image_comparison folder, image processing techniques are applied to prepare images for comparison. Each pair of images is then compared using Structural Similarity Index (SSIM), Perceptual Hash (Phash), and Mean Squared Error (MSE). The comparison results in a score for each image pair, allowing for evaluation of image matching.

Dockerization
A Dockerfile is included to containerize the project and its dependencies. Docker Compose is utilized to orchestrate the execution of the code alongside an IPFS local node, facilitating local access to images stored on IPFS.
