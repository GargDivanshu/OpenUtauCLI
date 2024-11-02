import json
import boto3
import requests
from botocore.exceptions import ClientError
import subprocess
import time
import sys
import os
import logging
import re
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def upload_file_to_s3(local_file, bucket, key):
    """Upload the specified file to S3."""
    # with open(local_file, 'r', encoding='utf-8') as utf8_file, open('ascii_file.txt', 'w', encoding='ascii', errors='ignore') as ascii_file:
    #     # Read the content from the UTF-8 file
    #     for line in utf8_file:
    #         # Write each line to the ASCII file
    #         ascii_file.write(line)
    try:
        print(f"Uploading {local_file} to s3://{bucket}/{key}...")
        s3_client.upload_file(local_file, bucket, key)
        print(f"File {local_file} uploaded successfully.")
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        exit(1)
        

def download_file_from_s3(bucket, key, local_output_file):
    """Download the specified file from S3 to local storage."""
    try:
        logger.info(f"Downloading {key} from S3 to {local_output_file}...")
        s3_client.download_file(bucket, key, local_output_file)
        logger.info(f"File {key} downloaded successfully to {local_output_file}")
    except ClientError as e:
        logger.error(f"Error downloading file {key}: {e}")
        raise e  # Raise exception to allow Lambda error handling
        
        
# oprimise for s3, lambda
def wait_for_file(bucket, key, s3_client, timeout=60, interval=5):
    """Wait for the specified file to become available in S3."""
    elapsed_time = 0
    while elapsed_time < timeout:
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
            logger.info(f"File {key} is now available in bucket {bucket}.")
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Use logging and exponential backoff instead of time.sleep
                logger.info(f"Waiting for file {key} in bucket {bucket} to be available...")
                time.sleep(interval)
                elapsed_time += interval
                interval = min(interval * 2, timeout - elapsed_time)  # Exponential backoff
            else:
                raise e  # Re-raise unexpected exceptions
    logger.error(f"File {key} did not become available within the timeout period.")
    return False


def clean_tmp_wav_file():
    """
    Finds the .wav file in the tmp directory, and renames it to ensure
    it ends with 'vocals.wav' by removing any characters or special symbols
    between 'vocals' and '.wav'.
    """
    # Determine the correct tmp directory path for both Unix and Windows
    tmp_dir = os.path.join("/tmp")  # This should adapt to "tmp" or "/tmp" as needed

    # Search for any .wav files in the tmp directory
    wav_files = glob.glob(os.path.join(tmp_dir, "*.wav"))
    
    if not wav_files:
        print(f"No WAV files found in {tmp_dir}.")
        return
    
    # Assume there's only one .wav file as per your logic
    file_path = wav_files[0]
    dir_name, original_filename = os.path.split(file_path)

    # Use regex to remove any characters after 'vocals' and before '.wav'
    new_filename = re.sub(r'(vocals).*?(\.wav)', r'\1.wav', original_filename)
    new_file_path = os.path.join(dir_name, new_filename)

    # Rename the file if a change was made
    if new_file_path != file_path:
        os.rename(file_path, new_file_path)
        print(f"Renamed file from {original_filename} to {new_filename}")
    else:
        print(f"No renaming needed for {original_filename}")


def check_files_and_directories(directory='/app'):
    """Check for files, count types, and the presence of OpenUtau executable."""
    try:
        # List all files and directories in the specified directory
        files_and_dirs = os.listdir(directory)
        logger.info(f"Contents of {directory}: {files_and_dirs}")

        # Initialize counters for different file types
        file_counts = {
            'dll': 0,
            'exe': 0,
            'txt': 0,
            'other': 0
        }
        openutau_present = False

        for item in files_and_dirs:
            full_path = os.path.join(directory, item)

            # Check for OpenUtau executable
            if item == 'OpenUtau':
                openutau_present = True
                logger.info("OpenUtau executable is present.")

            # Count file types based on extensions
            if os.path.isfile(full_path):
                if item.endswith('.dll'):
                    file_counts['dll'] += 1
                elif item.endswith('.exe'):
                    file_counts['exe'] += 1
                elif item.endswith('.txt'):
                    file_counts['txt'] += 1
                else:
                    file_counts['other'] += 1

        # Log the counts for each file type
        logger.info(f"DLL files count: {file_counts['dll']}")
        logger.info(f"Executable files count: {file_counts['exe']}")
        logger.info(f"Text files count: {file_counts['txt']}")
        logger.info(f"Other files count: {file_counts['other']}")

        if not openutau_present:
            logger.warning("OpenUtau executable is NOT present.")
        
    except Exception as e:
        logger.error(f"Error checking files and directories: {e}")


def notify_system_api(song_id, stage, action, file_name=None, err_msg=None, receipt_handle=None):
    """Notify the system API of the process status."""
    try:
        response = requests.post(
            # add to config 
            'https://85iufrg71j.execute-api.ap-south-1.amazonaws.com/v1/webhook/update-status',
            json={
                "songID": song_id,
                "stage": stage,
                "action": action,
                "fileName": file_name,
                "errMsg": err_msg,
                "receiptHandle": receipt_handle
            }
        )
        payload_data = {
                "songID": song_id,
                "stage": stage,
                "action": action,
                "fileName": file_name,
                "errMsg": err_msg,
                "receiptHandle": receipt_handle
            }
        response.raise_for_status()
        print(json.dumps(payload_data, indent="4"))
        print(response.json())
        print(f"{action.capitalize()} status notified successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to notify {action} status: {e}")