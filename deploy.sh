#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <image_name> <ip_addr>"
    exit 1
fi

IMAGE_NAME=$1
IP_ADDR=$2

# Step 1: Build the Docker image
echo "Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME -f DOCKER/Dockerfile .
if [ $? -ne 0 ]; then
    echo "Error: Docker build failed."
    exit 1
fi

# Step 2: Save the Docker image as a tar.gz file
echo "Saving Docker image to tar.gz file..."
docker save $IMAGE_NAME | gzip > ${IMAGE_NAME}.tar.gz
if [ $? -ne 0 ]; then
    echo "Error: Failed to save Docker image."
    exit 1
fi

# Step 3: Transfer the tar.gz file to the EC2 instance
echo "Transferring ${IMAGE_NAME}.tar.gz to EC2 instance at ${IP_ADDR}..."
scp -i L3_keypair.pem ${IMAGE_NAME}.tar.gz ec2-user@${IP_ADDR}:~/L3
if [ $? -ne 0 ]; then
    echo "Error: File transfer failed."
    exit 1
fi

echo "Deployment script completed successfully!"
