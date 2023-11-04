# Use the official Go image as a parent image
FROM golang:latest

# Set the working directory inside the container
WORKDIR /app


# Copy the local Go script into the container
COPY main.go ./
COPY go.mod ./
RUN go mod download


#COPY FebruaryClean.csv /data/

# Build the Go application
RUN CGO_ENABLED=0 GOOS=linux go build -o main

# Set the command to run the Go application
CMD ["./main"]

