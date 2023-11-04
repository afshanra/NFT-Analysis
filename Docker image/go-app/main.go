package main

import (
	"context"
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"mime"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func main() {
	csvFilePath := "/data/nft.csv"
	errorCsvFilePath := "/data/error_file.csv"
	outputFilePath := "/data/output.txt"

	// Create or open the output file for writing
	outputFile, err := os.Create(outputFilePath)
	if err != nil {
		log.Fatalf("Error creating output file: %v", err)
	}
	defer outputFile.Close()

	// Redirect standard output to both the console and the output file
	multiWriter := io.MultiWriter(os.Stdout, outputFile)
	log.SetOutput(multiWriter)

	file, err := os.Open(csvFilePath)
	if err != nil {
		log.Fatalf("Error opening CSV file: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)

	counter := 0

	// Create an error CSV file to store error records
	errorFile, err := os.Create(errorCsvFilePath)
	if err != nil {
		log.Fatalf("Error creating error CSV file: %v", err)
	}
	defer errorFile.Close()

	errorWriter := csv.NewWriter(errorFile)
	defer errorWriter.Flush()

	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}

		if err != nil {
			log.Fatalf("Error reading CSV record: %v", err)
		}

		// Skip the row if either of the URLs is empty
		if record[13] == "" || record[15] == "" {
			log.Printf("Skipping empty URL for record %d", counter)

			// Save the entire record with empty URLs to the error CSV file
			errorWriter.Write(record)
			errorWriter.Flush()

			continue
		}

		assetID := record[1]

		// Download 'opensea' images
		err = downloadImage(record[13], fmt.Sprintf("opensea/%s_opensea", assetID), counter)
		if err != nil {
			log.Printf("Error downloading opensea image: %v", err)

			// Save the entire record with download error to the error CSV file
			errorWriter.Write(record)
			errorWriter.Flush()
		}

		// Download 'original' images
		err = downloadImage(record[15], fmt.Sprintf("original/%s_original", assetID), counter)
		if err != nil {
			log.Printf("Error downloading original image: %v", err)

			// Save the entire record with download error to the error CSV file
			errorWriter.Write(record)
			errorWriter.Flush()
		}

		counter++
	}

	log.Println("Program completed successfully!")
}

func downloadImage(url string, savePath string, counter int) error {
	// Corrected the savePathWithExt to use /data directory
	savePathWithExt := fmt.Sprintf("/data/%s", savePath)

	// Check if URL contains "ipfs"
	if strings.HasPrefix(url, "ipfs://") {
		ipfsHash := url[len("ipfs://"):]
		ipfsGatewayURL := "http://ipfs:8080/ipfs/" + ipfsHash
		err := saveImage(ipfsGatewayURL, savePathWithExt, counter)
		if err != nil {
			// If downloading from the local gateway fails, try using ipfs.io
			ipfsIoURL := "https://ipfs.io/ipfs/" + ipfsHash
			err = saveImage(ipfsIoURL, savePathWithExt, counter)
			if err != nil {
				return err
			}
		}
	} else if strings.Contains(url, "/ipfs/") {
		ipfsGatewayURL := "http://ipfs:8080" + url[strings.Index(url, "/ipfs/"):]
		err := saveImage(ipfsGatewayURL, savePathWithExt, counter)
		if err != nil {
			// If downloading from the local gateway fails, try using ipfs.io
			ipfsIoURL := "https://ipfs.io" + url[strings.Index(url, "/ipfs/"):]
			err = saveImage(ipfsIoURL, savePathWithExt, counter)
			if err != nil {
				return err
			}
		}
	} else {
		err := saveImage(url, savePathWithExt, counter)
		if err != nil {
			return err
		}
	}
	return nil
}

func saveImage(url string, savePathWithExt string, counter int) error {
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return err
	}

	response, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer response.Body.Close()

	// Extract the file extension from the URL
	fileExt := getFileExtension(url)

	// If file extension is empty, get it from the response header
	if fileExt == "" {
		contentType := response.Header.Get("Content-Type")
		exts, err := mime.ExtensionsByType(contentType)
		if err == nil && len(exts) > 0 {
			fileExt = exts[0]
		}
	}

	// If the file extension is still empty, default to ".png"
	if fileExt == "" {
		fileExt = ".png"
	}

	// Create necessary directories
	err = os.MkdirAll(filepath.Dir(savePathWithExt), os.ModePerm)
	if err != nil {
		return err
	}

	file, err := os.Create(savePathWithExt)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = io.Copy(file, response.Body)
	if err != nil {
		return err
	}

	fmt.Printf("Successfully saved image %d: %s\n", counter, savePathWithExt)

	return nil
}

func getFileExtension(url string) string {
	// Extract the file extension from the URL
	fileExt := filepath.Ext(url)
	if fileExt != "" {
		return fileExt
	}
	return ""
}
