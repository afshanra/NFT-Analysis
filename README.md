 The Data-Collection Folder Includes The Following Scripts:

1) retrieve_opensea_events.py: Fetches NFT data for a given time frame and saves it to data.csv. Use the following command to run the script:

              python retrieve_opensea_events.py -s "2022-04-20 21:00" -e "2022-04-20 22:00"

2) select_random_nfts.py: Fetches random NFT data for each two hours within a specified date range. Use the following command to run the script:

              python select_random_nfts.py --start_date "2022-04-20 00:00" --end_date "2022-04-30 00:00"

   
3) config.py: includes API keys for OpenSea. Configure your API keys in this file to access OpenSea data.


The Download-Images Folder Includes A Go Script:

nft_image_downloader.go: Downloads NFT images from a CSV file and stores them in designated folders. Run the script using:

        go run nft_image_downloader.go


The Docker-Image Contains Docker-Related Files:

1) docker-compose.yml: Defines two Docker containers - one for running the Go script and one for an IPFS local container.
2) Dockerfile: Used to build the Go container.
3) nft.csv: A sample CSV file for use with the nft_image_downloader.go script.

DOCKER SETUP
To use the provided Docker containers, make sure you have Docker installed. Use the following steps:


1) Navigate to the docker-image directory.

2) Run the following commands to build and start the containers:

        docker-compose build
           docker-compose up -d

