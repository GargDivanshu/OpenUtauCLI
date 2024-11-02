import json
import boto3
import requests
from botocore.exceptions import ClientError
import subprocess
import time
import sys
import os
import logging
from rich import print
import re
import glob
from helpers import upload_file_to_s3, download_file_from_s3, wait_for_file, clean_tmp_wav_file, notify_system_api, check_files_and_directories


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# AWS & LAMBDA related keys
bucket_name = "singing-pipeline-eng-storage"
LAMBDA_STATIC_MIDI_FILE_PATH = "static/final.mid"
LAMBDA_STATIC_LYRICS_FILE_PATH = "static/lyrics.txt"

# Create AWS clients
s3_client = boto3.client('s3', region_name='ap-south-1')
lambda_client = boto3.client('lambda', region_name='ap-south-1')

# OPENUTAUCLI related envs
OU_INFERENCE_LOCAL_MIDI_PATH = "/tmp/final.mid" # to be 
OU_INFERENCE_LOCAL_LYRICS_PATH = "/tmp/lyrics.txt"
OU_SINGER_NUMBER = "1"
OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH = "/tmp/"
OU_FINAL_FILENAME = ""
OU_INFERENCE_LOCAL_EXPORT_PATH = ""
# os.path.join(OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH, OU_FINAL_FILENAME + ".wav")





 

def lambda_handler(event, context):
    """AWS Lambda handler function.
    Lyrics coming form payload are not being used here
    Here lyrics present in s3::singing-pipeline-eng-storage/static/lyrics.txt
    are being used for testing but when 
    Utau compatible lyrics will be received 
    from payload (currently eng lyrics - Non Utua compatible are being received)
    we will change the lambda flow
    """

    try:
        # Ensure MIDI file is available in S3
        if wait_for_file(bucket_name, LAMBDA_STATIC_MIDI_FILE_PATH, s3_client):
            download_file_from_s3(bucket_name, LAMBDA_STATIC_MIDI_FILE_PATH, OU_INFERENCE_LOCAL_MIDI_PATH)
        else:
            logger.error("MIDI file did not become available within the expected time.")
            return {"statusCode": 404, "body": "MIDI file not available"}
        
        check_files_and_directories("/app")

        # Process each record
        for record in event['Records']:
            try:
                # Parsing SQS message
                body = json.loads(record['body'])
                receipt_handle = record['receiptHandle']
                song_id = body.get("songID")
                OU_FINAL_FILENAME = f"song_{song_id}_vocals"
                OU_INFERENCE_LOCAL_EXPORT_PATH = os.path.join(OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH, f"{OU_FINAL_FILENAME}.wav")
                
                notify_system_api(song_id, "utau_inference", "start", None, None)
                
                # Download lyrics file for each record
                if wait_for_file(bucket_name, LAMBDA_STATIC_LYRICS_FILE_PATH, s3_client):
                    download_file_from_s3(bucket_name, LAMBDA_STATIC_LYRICS_FILE_PATH, OU_INFERENCE_LOCAL_LYRICS_PATH)
                else:
                    logger.error("Lyrics file did not become available.")
                    continue  # Skip to next record if lyrics file is not available

                # Run processing
                run_openutau(OU_FINAL_FILENAME, OU_INFERENCE_LOCAL_EXPORT_PATH)
                
                time.sleep(2)
                clean_tmp_wav_file()
                time.sleep(2)

                # Upload processed file to S3
                # LAMBDA SPECIFIC CHANGE :
                
                upload_file_to_s3(OU_INFERENCE_LOCAL_EXPORT_PATH, bucket_name, f"utau_inference/{OU_FINAL_FILENAME}.wav")
                
                notify_system_api(song_id, "utau_inference", "end", f"{OU_FINAL_FILENAME}.wav", None, receipt_handle)


            except Exception as e:
                logger.error(f"Error processing record for song_id {song_id}: {e}")
                notify_system_api(song_id, "utau_inference", "err", None, e, None)

            finally:
                # Clean up lyrics file after each record
                if os.path.exists(OU_INFERENCE_LOCAL_LYRICS_PATH):
                    os.remove(OU_INFERENCE_LOCAL_LYRICS_PATH)
                    logger.info(f"Deleted lyrics file: {OU_INFERENCE_LOCAL_LYRICS_PATH}")
                ustx_file_path = os.path.join("/tmp", f"{OU_FINAL_FILENAME}.ustx")
                wav_file_path = os.path.join("/tmp", f"{OU_FINAL_FILENAME}.wav")

                # Clean up .ustx and .wav files if they exist
                if os.path.exists(ustx_file_path):
                    os.remove(ustx_file_path)
                    logger.info(f"Deleted USTX file: {ustx_file_path}")

                if os.path.exists(wav_file_path):
                    os.remove(wav_file_path)
                    logger.info(f"Deleted WAV file: {wav_file_path}")

        # Clean up MIDI file after processing all records
        if os.path.exists(OU_INFERENCE_LOCAL_MIDI_PATH):
            os.remove(OU_INFERENCE_LOCAL_MIDI_PATH)
            logger.info(f"Deleted MIDI file: {OU_INFERENCE_LOCAL_MIDI_PATH}")

        return {"statusCode": 200, "body": "Processing completed successfully!"}

    except Exception as e:
        # This happened outside of Records array so cannot use systemAPI as it is 
        # NOT bound to any single songID
        logger.error(f"Critical error in lambda_handler: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}

                
                
# DUMMY PAYLOAD FOR LOCAL TESTING
payload = {
            "Records": [
                {
                    "messageId": "unique-message-id",
                    "receiptHandle": "MessageReceiptHandle",
                    "body": json.dumps({"fileName": None, "songID": 107, "lyrics": "Jingle"}),
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


def run_openutau(project_name, export_wav_path):
    p = False
    try:
        print("Running OpenUtau")
        # Start OpenUtau with --init, capturing stdout and stderr
        # as said by abhishek this below is wrong way of finding if a file is executable or not
        # if os.access('/app/OpenUtau', os.X_OK):
        #     print("OpenUtau is executable.")
        # else:
        #     print("OpenUtau is NOT executable.")
        #     return     
            
        process = subprocess.Popen(
            ["/app/OpenUtau", "--init"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        print("Subprocess started:", process.pid)
        logging.info("Subprocess started:", process.pid)
        
        print("Subprocess started...")
        
        
        # Add a small delay to allow OpenUtau to initialize and output text
        time.sleep(15)
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
            output = process.stdout.readline  # Read one character at a time

            

                    
            if not output:
                print ("Output not ready")
                logging.info("OUtput not ready")
                return
                    
            if output:
                print("Accumulating output")
                logging.info("Accumulating output")
                # Accumulate output until a newline
                accumulated_output += output
                print(output.strip())
                sys.stdout.write(output.strip())  # Print in real-time to avoid buffering
                sys.stdout.flush()
                # Send '--init' only once when '> ' prompt is detected
                if '> ' in accumulated_output and not init_sent:
                    print("Detected '> ' prompt; sending '--init'")
                    logging.info("Detected '> ' prompt; sending '--init'")
                    process.stdin.write("--init\n")
                    process.stdin.flush()
                    init_sent = True  # Set flag to avoid re-sending
                    accumulated_output = ""  # Clear accumulated output
                # Respond to project selection prompt after initialization
                elif "Do you want to [1] Open an existing project or [2] Start a new project?" in accumulated_output:
                    print("Detected project selection prompt; sending '2'")
                    logging.info("Detected project selection prompt; sending '2'")
                    process.stdin.write("2\n")
                    process.stdin.flush()
                    project_selected = True  # Set flag after project selection
                    accumulated_output = ""  # Clear accumulated output
                # Send MIDI import command after project selection is complete
                elif '> ' in accumulated_output and project_selected and not midi_imported:
                    print(f"Detected '> ' prompt; sending '--import --midi {OU_INFERENCE_LOCAL_MIDI_PATH}'")
                    logging.info(f"Detected '> ' prompt; sending '--import --midi {OU_INFERENCE_LOCAL_MIDI_PATH}")
                    process.stdin.write(f"--import --midi {OU_INFERENCE_LOCAL_MIDI_PATH}\n")
                    process.stdin.flush()
                    midi_imported = True  # Set flag to avoid re-sending MIDI import
                    accumulated_output = ""  # Clear accumulated output
                # Send lyrics import command after MIDI import is complete
                elif '> ' in accumulated_output and midi_imported and not lyrics_imported:
                    print(f"Detected '> ' prompt; sending '--lyrics {OU_INFERENCE_LOCAL_LYRICS_PATH}'")
                    logging.info(f"Detected '> ' prompt; sending '--lyrics {OU_INFERENCE_LOCAL_LYRICS_PATH}'")
                    process.stdin.write(f"--lyrics {OU_INFERENCE_LOCAL_LYRICS_PATH}\n")
                    process.stdin.flush()
                    lyrics_imported = True  # Set flag to avoid re-sending lyrics import
                    accumulated_output = ""  # Clear accumulated output
                # Respond to part number selection prompt for adding lyrics
                elif "Select a part number to add lyrics:" in accumulated_output:
                    print("Detected part number prompt; entering '1'")
                    logging.info("Detected part number prompt; entering '1'")
                    process.stdin.write("1\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # Send track removal command after lyrics import
                elif '> ' in accumulated_output and lyrics_imported and not track_removed:
                    print("Detected '> ' prompt; sending '--track --remove'")
                    logging.info("Detected '> ' prompt; sending '--track --remove'")
                    process.stdin.write("--track --remove\n")
                    process.stdin.flush()
                    track_removed = True  # Set flag to avoid re-sending track removal
                    accumulated_output = ""  # Clear accumulated output
                # Respond to track number selection prompt
                elif "Enter the number of the track to remove:" in accumulated_output and not track_number_entered:
                    print("Detected track number prompt; entering '1'")
                    logging.info("Detected track number prompt; entering '1'")
                    process.stdin.write("1\n")
                    process.stdin.flush()
                    track_number_entered = True  # Set flag after entering track number
                    accumulated_output = ""  # Clear accumulated output
                # Send track update command after track removal
                elif '> ' in accumulated_output and track_number_entered and not track_updated:
                    print("Detected '> ' prompt; sending '--track --update'")
                    logging.info("Detected '> ' prompt; sending '--track --update'")
                    process.stdin.write("--track --update\n")
                    process.stdin.flush()
                    track_updated = True  # Set flag to avoid re-sending track update
                    accumulated_output = ""  # Clear accumulated output
                # Respond to track update selection prompt
                elif "Select a track to update:" in accumulated_output:
                    print("Detected track update selection prompt; entering '1'")
                    logging.info("Detected track update selection prompt; entering '1'")
                    process.stdin.write("1\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # Respond to singer selection prompt
                elif "Select a singer by number:" in accumulated_output:
                    print(f"Detected singer selection prompt; entering '{OU_SINGER_NUMBER}'")
                    logging.info(f"Detected singer selection prompt; entering '{OU_SINGER_NUMBER}'")
                    process.stdin.write(f"{OU_SINGER_NUMBER}\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # Respond to phonemizer selection prompt
                elif "Enter the phonemizer name to apply:" in accumulated_output:
                    print("Detected phonemizer selection prompt; entering 'OpenUtau.Core.DiffSinger.DiffSingerEnglishPhonemizer'")
                    logging.info("Detected phonemizer selection prompt; entering 'OpenUtau.Core.DiffSinger.DiffSingerEnglishPhonemizer'")
                    process.stdin.write("OpenUtau.Core.DiffSinger.DiffSingerEnglishPhonemizer\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                elif "> " in accumulated_output and not pitch_processing:
                    print("Detected '> ' prompt; Sending '--process --pitch'")
                    logging.info("Detected '> ' prompt; Sending '--process --pitch'")
                    time.sleep(2)
                    process.stdin.write("--process --pitch\n")
                    process.stdin.flush()
                    time.sleep(2)
                    accumulated_output = ""
                    # breakpoint()

                elif "Select a part to process:" in accumulated_output and not pitch_processing:
                    print("Detected Part selection prompt; entering '1'")
                    logging.info("Detected Part selection prompt; entering '1'")
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
                    # print(f"Detected directory path prompt; entering '{OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH}'")
                    process.stdin.write(f"{OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH}\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # Respond to file name prompt for saving the project
                elif "Enter the name for the project file (without extension):" in accumulated_output and not_saved:
                    # print(f"Detected file name prompt; entering '{FILE_NAME}'")
                    process.stdin.write(f"{project_name}\n")
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
                    print(f"[red]Detected WAV export path prompt; entering '{export_wav_path}'[/red]")
                    process.stdin.write(f"{export_wav_path}\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                    export_fully_completed = True  # Set flag to avoid re-sending export path
                     
                # elif p and export_fully_completed:
                #     print("[red]Detected '> ' prompt; sending '--exit'[/red]")
                #     # process.stdin.write(OU_INFERENCE_LOCAL_EXPORT_PATH)
                #     # process.stdin.flush()
                #     p = False
                
                elif p and export_fully_completed and '> ' in accumulated_output:
                    print("[red]Detected '> ' prompt; sending '--exit'[/red]")
                    logging.info("[red]Detected '> ' prompt; sending '--exit'[/red]")
                    time.sleep(2)
                    p = False
                    
                elif "Project has been successfully exported to WAV" in accumulated_output:
                    return   
            # Break the loop if export is fully completed
                if export_fully_completed:
                    break

    # Flush the process output if buffering issues persist
                process.stdout.flush()                 
                    
            # Check if process has ended
            if process.poll() is not None:
                print("Process ended.")
                break
    except Exception as e:
        print("Error encountered:", e)
    finally:
        if process:
            process.terminate()  # Ensure the process is terminated     
           
            
# UNCOMMENT FOR LOCAL LAMBDA TESTING  
# response = lambda_handler(payload, None)
# print(response)




# UNCOMMENT FOR OPENUTAUCLI - ONLY TESTING
# # Global Paths
# Abhishek's env variables
# OU_INFERENCE_LOCAL_MIDI_PATH = "C:\\Users\\abhis\\Downloads\\simple_midi.mid"
# OU_INFERENCE_LOCAL_LYRICS_PATH = "C:\\Users\\abhis\\Downloads\\simple_lyrics.txt"
# save_dir = "C:\\Users\\abhis\\Downloads\\project"
# wav_export_path = "C:\\Users\\abhis\\Downloads\\project\\output.wav"
# OU_SINGER_NUMBER = "1"
# project_file_name = "AMAN_MEET"

# Divanshu's env variables
# OU_INFERENCE_LOCAL_MIDI_PATH = "C:\\Users\\divan\\Downloads\\midi_export.mid"
# OU_INFERENCE_LOCAL_LYRICS_PATH = "C:\\Users\\divan\\OneDrive\\Desktop\\AEOS\\floating_on_the_trial.txt"
# save_dir = "C:\\Users\\divan\\Downloads"
# project_file_name = "floating_on_the_trial"
# wav_export_path = os.path.join(save_dir, project_file_name + ".wav")
# OU_SINGER_NUMBER = "1"


    

# Run the function
# run_openutau(project_file_name, wav_export_path)
