#!/bin/bash

# Check if ENV variable is set
if [ -z "$ENV" ]; then
  echo "Error: ENV variable is not set. Please set it to 'staging' or 'production'."
  exit 1
fi

# Log the environment being used
echo "Fetching files for environment: $ENV"

# Fetch files from S3 bucket based on the environment
aws s3 cp s3://cadbury-carol-ci-cd-prod-24/$ENV/ /app --recursive

# Verify files were downloaded
if [ $? -eq 0 ]; then
  echo "Files successfully downloaded for environment: $ENV"
else
  echo "Failed to download files for environment: $ENV"
  exit 1
fi
