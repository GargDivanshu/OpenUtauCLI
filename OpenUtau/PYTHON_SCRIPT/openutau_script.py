import json
import boto3
import requests
import botocore.exceptions
import subprocess
import time
import sys
import os
import rich


# PLS SCROLL DOWN FOR OPENUTAU SCRIPT : LAMBDA CODE IS STOPPED RN


# lambda_arn = "arn:aws:lambda:ap-south-1:108782080917:function:singing-vocal"
bucket_name = "singing-pipeline-eng-storage"
midi_file = "static/final.mid"
lyrics_file = "static/lyrics.txt"

# Create AWS clients
s3_client = boto3.client('s3', region_name='ap-south-1')
lambda_client = boto3.client('lambda', region_name='ap-south-1')



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
        print("Downloading the processed WAV file from S3...")
        s3_client.download_file(bucket, key, local_output_file)
        print(f"Processed WAV file downloaded to {local_output_file}")
    except Exception as e:
        print(f"Error downloading the processed WAV file: {e}")
        exit(1)
        
        
# oprimise for s3, lambda
def wait_for_file(bucket, key, timeout=60, interval=5):
    """Wait for the specified file to become available in S3."""
    elapsed_time = 0
    while elapsed_time < timeout:
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"Waiting for file {key} in bucket {bucket} to be available...")
                time.sleep(interval)
                elapsed_time += interval
            else:
                raise e
    return False



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
        response.raise_for_status()
        print(f"{action.capitalize()} status notified successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to notify {action} status: {e}")
        
MIDI_FILE_PATH = ""
LYRICS_FILE_PATH = ""
SINGER_NUMBER = "2"
PROJECT_SAVE_PATH = ""
FILENAME = ""

def lambda_handler(event, context): 
    
    """AWS Lambda handler function."""
    try:
        
        # LOCAL_MIDI_FILE = "/tmp/final.mid"
        # LOCAL_LYRICS_FILE = "/tmp/lyrics.txt"
        # LOCAL_WAV_OUTPUT_PATH = "/tmp/output.wav"
        LOCAL_MIDI_FILE = "final.mid"
        LOCAL_LYRICS_FILE = "lyrics.txt"
        # LOCAL_WAV_OUTPUT_PATH = "output.wav"
        LOCAL_WAV_OUTPUT_PATH = "AMAN_MEET__.wav"      
          
        
        if wait_for_file(bucket_name, midi_file):
            download_file_from_s3(bucket_name, midi_file, LOCAL_MIDI_FILE)
        else:
            print("Error: The output file did not become available within the expected time.")
            exit(1)
                
                
        # HIT SYSTEM API HERE TO ENSURE YOU LET THEM SYSTEM KNOW THE `utau_inference` stage is started
        # implement here . . . 
        
        # Extract paths from the event
        for record in event['Records']:
            print("Record started!!")
            # Extract message data from the SQS message
            
            
            # add a second try - catch:
            
            
            
            body = json.loads(record['body'])
            receipt_handle = record['receiptHandle']
            song_id = body.get("songID")  # Set default songID if not present
            lyrics = body.get("lyrics")
            file_name = body.get("fileName", None)
            
            print(f"body: {body}")
            
            
            
            # lyrics -> txt storage in tmp 

            # Notify system API that `utau_inference` stage is starting
            notify_system_api(song_id, "utau_inference", "start", receipt_handle=None)

            
            # weird not downloading
            # if wait_for_file(bucket_name, LOCAL_LYRICS_FILE):
            #     download_file_from_s3(bucket_name, lyrics_file, LOCAL_LYRICS_FILE)
            # else:
            #     print("Error: The output file did not become available within the expected time.")
            #     exit(1)
                
            MIDI_FILE_PATH = LOCAL_MIDI_FILE
            LYRICS_FILE_PATH = LOCAL_LYRICS_FILE
            
            
                
            
            # run_openutau()
            
            # change the filename 
            # {song_id|_inference.wav
            upload_file_to_s3(LOCAL_WAV_OUTPUT_PATH, bucket_name, f"/utau_inference/{LOCAL_WAV_OUTPUT_PATH}")

            # After processing, notify system API that `utau_inference` stage is ending
            notify_system_api(song_id, "utau_inference", "end", file_name=LOCAL_WAV_OUTPUT_PATH, receipt_handle=receipt_handle)
            
        
            # delete the tmp file after for loop 
        # delete the static files 
        
        return {
            "statusCode": 200,
            "body": json.dumps("Processing completed successfully!")
        }
    except Exception as e:
        # TypeError: Object of type set is not JSON serializable - solve 
        notify_system_api(song_id, "utau_inference", "error", file_name=None, receipt_handle=None, err_msg="got error - string err")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error: {str(e)}")
        }

payload = {
            "Records": [
                {
                    "messageId": "unique-message-id",
                    "receiptHandle": "MessageReceiptHandle",
                    "body": json.dumps({"fileName": None, "songID": 105, "lyrics": "Jingle"}),
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": str(int(time.time() * 1000)),
                        "SenderId": "108782080917",
                        "ApproximateFirstReceiveTimestamp": str(int(time.time() * 1000))
                    },
                    "messageAttributes": {},
                    "md5OfBody": "md5_of_body_placeholder",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:ap-south-1:108782080917:MyQueue",  # Replace with your SQS ARN if used
                    "awsRegion": "ap-south-1"
                }
            ]
        }

# response = lambda_handler(payload, None)
# print(response)


# # Global Paths
# Abhishek's env variables
# MIDI_FILE_PATH = "C:\\Users\\abhis\\Downloads\\simple_midi.mid"
# LYRICS_FILE_PATH = "C:\\Users\\abhis\\Downloads\\simple_lyrics.txt"
# PROJECT_SAVE_PATH = "C:\\Users\\abhis\\Downloads\\project"
# EXPORT_WAV_PATH = "C:\\Users\\abhis\\Downloads\\project\\output.wav"
# SINGER_NUMBER = "1"
# FILENAME = "AMAN_MEET"
# Divanshu's env variables
MIDI_FILE_PATH = "C:\\Users\\divan\\Downloads\\midi_export.mid"
LYRICS_FILE_PATH = "C:\\Users\\divan\\OneDrive\\Desktop\\AEOS\\backyard.txt"
PROJECT_SAVE_PATH = "C:\\Users\\divan\\Downloads"
FILENAME = "backyard_midi_export"
EXPORT_WAV_PATH = os.path.join(PROJECT_SAVE_PATH, FILENAME + ".wav")
SINGER_NUMBER = "1"


    
def run_openutau():
    p = False
    try:
        # Start OpenUtau with --init, capturing stdout and stderr
        process = subprocess.Popen(
            ["OpenUtau.exe", "--init"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        # Add a small delay to allow OpenUtau to initialize and output text
        time.sleep(1)
        # Continuously read output line-by-line
        accumulated_output = ""
        init_sent = False          # Flag to track if '--init' has been sent
        project_selected = False   # Flag to track if project selection is complete
        midi_imported = False      # Flag to track MIDI import command
        lyrics_imported = False    # Flag to track lyrics import command
        track_removed = False      # Flag to track track removal
        track_number_entered = False # Flag to confirm track number entry
        track_updated = False      # Flag to track track update
        export_completed = False   # Flag to track export completion
        not_saved = True           # Flag to track if project has been saved
        export_fully_completed = False
        pitch_processing = False
        while True:
            output = process.stdout.read(1)  # Read one character at a time
                    
                    
            if output:
                # Accumulate output until a newline
                accumulated_output += output
                sys.stdout.write(output)  # Print in real-time to avoid buffering
                sys.stdout.flush()
                # Send '--init' only once when '> ' prompt is detected
                if '> ' in accumulated_output and not init_sent:
                    print("Detected '> ' prompt; sending '--init'")
                    process.stdin.write("--init\n")
                    process.stdin.flush()
                    init_sent = True  # Set flag to avoid re-sending
                    accumulated_output = ""  # Clear accumulated output
                # Respond to project selection prompt after initialization
                elif "Do you want to [1] Open an existing project or [2] Start a new project?" in accumulated_output:
                    print("Detected project selection prompt; sending '2'")
                    process.stdin.write("2\n")
                    process.stdin.flush()
                    project_selected = True  # Set flag after project selection
                    accumulated_output = ""  # Clear accumulated output
                # Send MIDI import command after project selection is complete
                elif '> ' in accumulated_output and project_selected and not midi_imported:
                    print(f"Detected '> ' prompt; sending '--import --midi {MIDI_FILE_PATH}'")
                    process.stdin.write(f"--import --midi {MIDI_FILE_PATH}\n")
                    process.stdin.flush()
                    midi_imported = True  # Set flag to avoid re-sending MIDI import
                    accumulated_output = ""  # Clear accumulated output
                # Send lyrics import command after MIDI import is complete
                elif '> ' in accumulated_output and midi_imported and not lyrics_imported:
                    print(f"Detected '> ' prompt; sending '--lyrics {LYRICS_FILE_PATH}'")
                    process.stdin.write(f"--lyrics {LYRICS_FILE_PATH}\n")
                    process.stdin.flush()
                    lyrics_imported = True  # Set flag to avoid re-sending lyrics import
                    accumulated_output = ""  # Clear accumulated output
                # Respond to part number selection prompt for adding lyrics
                elif "Select a part number to add lyrics:" in accumulated_output:
                    print("Detected part number prompt; entering '1'")
                    process.stdin.write("1\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # Send track removal command after lyrics import
                elif '> ' in accumulated_output and lyrics_imported and not track_removed:
                    print("Detected '> ' prompt; sending '--track --remove'")
                    process.stdin.write("--track --remove\n")
                    process.stdin.flush()
                    track_removed = True  # Set flag to avoid re-sending track removal
                    accumulated_output = ""  # Clear accumulated output
                # Respond to track number selection prompt
                elif "Enter the number of the track to remove:" in accumulated_output and not track_number_entered:
                    print("Detected track number prompt; entering '1'")
                    process.stdin.write("1\n")
                    process.stdin.flush()
                    track_number_entered = True  # Set flag after entering track number
                    accumulated_output = ""  # Clear accumulated output
                # Send track update command after track removal
                elif '> ' in accumulated_output and track_number_entered and not track_updated:
                    print("Detected '> ' prompt; sending '--track --update'")
                    process.stdin.write("--track --update\n")
                    process.stdin.flush()
                    track_updated = True  # Set flag to avoid re-sending track update
                    accumulated_output = ""  # Clear accumulated output
                # Respond to track update selection prompt
                elif "Select a track to update:" in accumulated_output:
                    print("Detected track update selection prompt; entering '1'")
                    process.stdin.write("1\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # Respond to singer selection prompt
                elif "Select a singer by number:" in accumulated_output:
                    print("Detected singer selection prompt; entering '1'")
                    process.stdin.write(f"{SINGER_NUMBER}\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # Respond to phonemizer selection prompt
                elif "Enter the phonemizer name to apply:" in accumulated_output:
                    print("Detected phonemizer selection prompt; entering 'OpenUtau.Core.DiffSinger.DiffSingerEnglishPhonemizer'")
                    process.stdin.write("OpenUtau.Core.DiffSinger.DiffSingerEnglishPhonemizer\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                elif "> " in accumulated_output and not pitch_processing:
                    print("Detected '> ' prompt; Sending '--process --pitch'")
                    time.sleep(2)
                    process.stdin.write("--process --pitch\n")
                    process.stdin.flush()
                    time.sleep(2)
                    accumulated_output = ""
                    # breakpoint()

                elif "Select a part to process:" in accumulated_output and not pitch_processing:
                    print("Detected Part selection prompt; entering '1'")
                    process.stdin.write("1\n")
                    process.stdin.flush()
                    pitch_processing = True
                    accumulated_output = ""
                # # SAVING
                # # Send save command after export is complete
                # elif '> ' in accumulated_output and not_saved:
                #     print("Detected '> ' prompt; sending '--save'")
                #     process.stdin.write("--save\n")
                #     process.stdin.flush()
                #     accumulated_output = ""  # Clear accumulated output
                # Respond to directory path prompt for saving the project
                elif "Enter the directory path where you want to save the project:" in accumulated_output and not_saved:
                    # print(f"Detected directory path prompt; entering '{PROJECT_SAVE_PATH}'")
                    process.stdin.write(f"{PROJECT_SAVE_PATH}\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # Respond to file name prompt for saving the project
                elif "Enter the name for the project file (without extension):" in accumulated_output and not_saved:
                    # print(f"Detected file name prompt; entering '{FILE_NAME}'")
                    process.stdin.write(f"{FILENAME}\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                    not_saved = False
                # Send export command after track update
                elif '> ' in accumulated_output and track_updated and not export_completed:
                    # print("Detected '> ' prompt; sending '--export --wav'")
                    time.sleep (2)
                    process.stdin.write("--export --wav\n")
                    process.stdin.flush()
                    export_completed = True  # Set flag to avoid re-sending export
                    accumulated_output = ""  # Clear accumulated output
                    time.sleep (10)
                    p = True
                    
                elif "Enter the path where you want to export the WAV file:" in accumulated_output and not export_fully_completed:
                    print()
                    print(f"[red]Detected WAV export path prompt; entering '{EXPORT_WAV_PATH}'[/red]")
                    process.stdin.write(f"{EXPORT_WAV_PATH}\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                    export_fully_completed = True  # Set flag to avoid re-sending export path
                     
                # elif p and export_fully_completed:
                #     print("[red]Detected '> ' prompt; sending '--exit'[/red]")
                #     # process.stdin.write(EXPORT_WAV_PATH)
                #     # process.stdin.flush()
                #     p = False
                
                elif p and export_fully_completed and '> ' in accumulated_output:
                    print("[red]Detected '> ' prompt; sending '--exit'[/red]")
                    time.sleep(2)
                    p = False
                    
                elif "Project has been successfully exported to WAV" in accumulated_output:
                    return                    
                    
            # Check if process has ended
            if process.poll() is not None:
                print("Process ended.")
                break
    except Exception as e:
        print("Error encountered:", e)
    finally:
        if process:
            process.terminate()  # Ensure the process is terminated
# Run the function
run_openutau()