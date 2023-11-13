 The "NFT sales data collection" Folder Includes The Following Scripts:

1) retrieve_opensea_events.py: Fetches NFT data for a given time frame and saves it to data.csv. Use the following command to run the script:

              python retrieve_opensea_events.py -s "2022-04-20 21:00" -e "2022-04-20 22:00"

2) select_random_nfts_skip_errors.py: Fetches random NFT data every two hours within a specified date range. Use the following command to run the script:

              select_random_nfts_skip_errors.py --start_date "2022-04-20 00:00" --end_date "2022-04-30 00:00"

   
3) config.py: includes API keys for OpenSea. Configure your API keys in this file to access OpenSea data.



