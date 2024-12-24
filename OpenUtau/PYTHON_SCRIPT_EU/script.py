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
from helpers import upload_file_to_s3,download_folder_from_s3, download_file_from_s3, wait_for_file, clean_tmp_wav_file, notify_system_api, check_files_and_directories
from tqdm import tqdm
import platform
from dotenv import load_dotenv
from datetime import datetime
from lyrics import analyze_lyrics_de
import time
from melody_generation import main_melody_generation
    
    
import os
import boto3
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

from config import Config, initialize_config


os.makedirs("/tmp/Logs", exist_ok=True)
os.makedirs("/tmp/OpenUtau", exist_ok=True)
os.makedirs("/tmp/OpenUtau/Logs", exist_ok=True)
# Load environment variables from .env file
load_dotenv()

# Configure logging
log_file = "/tmp/Logs/openutau_process.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
region_lang = os.getenv("REGION_LANG")

# Initialize the configuration
config = initialize_config()

# Assign global variables based on the config struct
BUCKET_NAME = config.BUCKET_NAME
bucket_name = BUCKET_NAME # For consistency with existing code, some nonsense @divanshu can we clean it up?
REGION_NAME = config.REGION_NAME
IS_LAMBDA_ENV = config.IS_LAMBDA_ENV
SQS_QUEUE_URL = config.SQS_QUEUE_URL
OU_INFERENCE_LOCAL_MIDI_PATH = config.OU_INFERENCE_LOCAL_MIDI_PATH
OU_INFERENCE_LOCAL_LYRICS_PATH = config.OU_INFERENCE_LOCAL_LYRICS_PATH
OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH = config.OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH
OU_SINGER_NUMBER = config.OU_SINGER_NUMBER
OU_FINAL_FILENAME = config.OU_FINAL_FILENAME
OU_INFERENCE_LOCAL_EXPORT_PATH = config.OU_INFERENCE_LOCAL_EXPORT_PATH
OU_INFERENCE_LOCAL_USTX_PATH = config.OU_INFERENCE_LOCAL_USTX_PATH
OU_LYRICS_JSON_PATH = config.OU_LYRICS_JSON_PATH


class PathManager:
    def __init__(self, song_id, export_filename):
        self.song_id = song_id
        self.export_filename = export_filename

        # Define local paths
        self.local_export_path = OU_INFERENCE_LOCAL_EXPORT_PATH
        self.local_midi_path = OU_INFERENCE_LOCAL_MIDI_PATH
        self.local_lyrics_path = OU_INFERENCE_LOCAL_LYRICS_PATH
        self.local_lyrics_json_path = OU_LYRICS_JSON_PATH
        self.local_log_path = f"/tmp/Logs/song_{self.song_id}_utaulogs.log"
        self.local_section_summary_path = "/tmp/section_summary.csv"
        self.local_system_log_path = f"/tmp/Logs/openutau_process.log"

        # Define S3 paths
        self.s3_export_path = f"utau_inference/{region_lang}/{self.export_filename}.wav"
        self.s3_log_path = f"Logs/{region_lang}/song_{self.song_id}/song_{self.song_id}_utaulogs.log"
        self.s3_midi_path = f"Logs/{region_lang}/song_{self.song_id}/{self.song_id}_midi.mid"
        self.s3_lyrics_txt_path = f"Logs/{region_lang}/song_{self.song_id}/{self.song_id}_lyrics.txt"
        self.s3_lyrics_json_path = f"Logs/{region_lang}/song_{self.song_id}/{self.song_id}_lyrics.json"
        self.s3_wav_duplicate_path = f"Logs/{region_lang}/song_{self.song_id}/{self.export_filename}.wav"
        self.s3_section_summary_path = f"Logs/{region_lang}/song_{self.song_id}/{self.song_id}_section_summary.csv"
        self.s3_system_log_path = f"Logs/{region_lang}/song_{self.song_id}/{self.song_id}_system_log.log"

        # Collect paths in a dictionary for convenience
        self.paths = {
            "utau_inference_wav": (self.local_export_path, self.s3_export_path),
            "utaulogs": (self.local_log_path, self.s3_log_path),
            "midi": (self.local_midi_path, self.s3_midi_path),
            # "lyrics_txt": (self.local_lyrics_path, self.s3_lyrics_txt_path),
            # "lyrics_json": (self.local_lyrics_json_path, self.s3_lyrics_json_path),
            "wav_duplicate": (self.local_export_path, self.s3_wav_duplicate_path),
            # "section_summary": (self.local_section_summary_path, self.s3_section_summary_path),
            "openutau_process": (self.local_system_log_path, self.s3_system_log_path)
        }

    def get_path_pairs(self):
        return self.paths

# Function to process uploads using the PathManager class
def process_and_upload_to_s3(song_id):
    path_manager = PathManager(song_id, OU_FINAL_FILENAME)
    paths = path_manager.get_path_pairs()

    for local_path, s3_path in paths.values():
        upload_file_to_s3(local_path, bucket_name, s3_path)


# Create AWS clients
sqs_client = boto3.client("sqs", region_name=REGION_NAME)
s3_client = boto3.client('s3', region_name=REGION_NAME)
lambda_client = boto3.client('lambda', region_name=REGION_NAME)

# os.path.join(OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH, OU_FINAL_FILENAME + ".wav")

def process_message(body):
    """Process a single message body from SQS."""
    global OU_FINAL_FILENAME, OU_INFERENCE_LOCAL_EXPORT_PATH, OU_SINGER_NUMBER, OU_INFERENCE_LOCAL_USTX_PATH, OU_LYRICS_JSON_PATH

    try:
        print("process fn started")

    
    

    
        song_id = body.get("songID")
        name = body.get("name")
        reason = body.get("reason")
        region = body.get("region")
        trackId = body.get("trackID")
        lyrics = body.get("lyrics")
        tag = body.get("tag")
        OU_FINAL_FILENAME = f"song_{song_id}_vocals"
        OU_INFERENCE_LOCAL_EXPORT_PATH = os.path.join("/tmp", f"{OU_FINAL_FILENAME}.wav")
        OU_INFERENCE_LOCAL_USTX_PATH = os.path.join("/tmp", f"{OU_FINAL_FILENAME}.ustx")
        # OU_LYRICS_JSON_PATH = os.path.join("/tmp", "lyrics.json")
        OU_LYRICS_JSON_PATH = "/tmp/lyrics.json"
        
        formatted_lyrics = ""
        syllable_breakdown = ''
        total_syllables = 0
        if region == "germany":
            start = time.monotonic()
            formatted_lyrics, syllable_breakdown, total_syllables = analyze_lyrics_de(lyrics)
            with open("/tmp/lyrics_readable.txt", "w", encoding="utf-8") as file:
                file.write(lyrics)
                
                
        output_file = "/tmp/lyrics.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(formatted_lyrics)
        end = time.monotonic()
        duration = (end_time - start_time)  
        logger.info("lyrics_process stats")
        logger.info(f"Start Time: {start_time:.2f}, End Time: {end_time:.2f}, Duration: {duration:.2f} seconds.")
        logger.info("============================================================")
        print(f"Lyrics processing took {end - start:.2f} seconds")
        
        # time.sleep(1)
        # lyrics_api_filename = f"lyrics/{song_id}_lyrics.json"
        # upload_file_to_s3(OU_LYRICS_JSON_PATH, BUCKET_NAME, lyrics_api_filename)
        # notify_lyrics_json_upload(song_id, f"{song_id}_lyrics.json") 
        
        start_time = time.monotonic()
        region_name = region.capitalize()
        vocal_midi_file_path = f"/tmp/{region}/vocals/{region_name}Track{trackId}MIDI.mid"
        backing_midi_file_path = f"/tmp/{region}/backing/{region_name}Track{trackId}ChordMIDI.mid"
        main_melody_generation(lyrics, 115, backing_midi_file_path, vocal_midi_file_path)
        end_time = time.monotonic()
        duration = (end_time - start_time)  
        logger.info("midimain() stats")
        logger.info(f"Start Time: {start_time:.2f}, End Time: {end_time:.2f}, Duration: {duration:.2f} seconds.")
        logger.info("============================================================")
        
        
        # lyrics_with_syllable, utau_lyrics = midimain() #this assumes lyrics are already present in /tmp/lyrics_readable.txt
        # print(lyrics_with_syllable, " lyrics_with_syllable")
        # print(utau_lyrics, " utau_lyrics")
        # output_file = "/tmp/lyrics.txt"
        # with open(output_file, "w", encoding="utf-8") as file:
        #     file.write(utau_lyrics)
        

        # print(f"UTAU lyrics written to {output_file}")
    
        # Run processing
        start_time = time.monotonic()
        run_openutau(OU_FINAL_FILENAME, OU_INFERENCE_LOCAL_EXPORT_PATH, song_id)
        end_time = time.monotonic()
        duration = (end_time - start_time)  
        logger.info("run_openutau stats")
        logger.info(f"Start Time: {start_time:.2f}, End Time: {end_time:.2f}, Duration: {duration:.2f} seconds.")
        logger.info("============================================================")
        
    
        time.sleep(2)
        clean_tmp_wav_file()
        time.sleep(2)
    
        # Upload processed file to S3
        
        start_time = time.monotonic()
        process_and_upload_to_s3(song_id)
        end_time = time.monotonic()
        duration = (end_time - start_time)  
        logger.info("process_and_upload_to_s3 stats")
        logger.info(f"Start Time: {start_time:.2f}, End Time: {end_time:.2f}, Duration: {duration:.2f} seconds.")
        logger.info("============================================================")
    
        # Clean up files

    
    except Exception as e:
        logger.error(f"Error processing record for song_id {song_id}: {str(e)}")
        notify_system_api(song_id, "utau_inference", "error", None, str(e), None) 
    
    finally:
        # Cleanup files
        files_to_delete = [
            OU_INFERENCE_LOCAL_LYRICS_PATH,
            OU_INFERENCE_LOCAL_MIDI_PATH,
            OU_INFERENCE_LOCAL_EXPORT_PATH,
            OU_INFERENCE_LOCAL_USTX_PATH,
            f"/tmp/Logs/song_{song_id}_utaulogs.log",
            # OU_LYRICS_JSON_PATH,
            # f"/tmp/section_summary.csv",
            # f"/tmp/lyrics_readable.txt"
        ]
        with open(f"/tmp/Logs/openutau_process.log", 'w') as file:
            pass  # Do nothing, just opening in 'w' mode clears the file

        print(f"All contents of the file Logs/openutau_process.log have been deleted.")
        
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Removed {file_path}")
                except Exception as remove_error:
                    logger.error(f"Failed to remove {file_path}: {remove_error}")

        return {
        "statusCode": 200,
        "body": json.dumps({"message": "Processing completed successfully."})
    }


 

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
        
        base_s3_path = "Lambda_Utau/"
        local_base_path = "/tmp/OpenUtau/"
        local_tmp_path = "/tmp/"
        os.makedirs(local_base_path, exist_ok=True)
        region = os.getenv('REGION_PROD')

        # Define folder mappings
        folders_to_download = {
            "Singers/": os.path.join(local_base_path, "Singers"),
            "Dependencies/": os.path.join(local_base_path, "Dependencies"),
            "Plugins/": os.path.join(local_base_path, "Plugins"),
            "germany/": os.path.join(local_tmp_path, "germany"),
            "romania/": os.path.join(local_tmp_path, "romania"),
        }
        
         # Download folders from S3
        for folder_key, local_output_dir in folders_to_download.items():
            print(f"Downloading {folder_key} to {local_output_dir}...")
            download_folder_from_s3(BUCKET_NAME, base_s3_path + folder_key, local_output_dir)
            print(f"Finished downloading {folder_key}")
            
        # region_specific_s3_path = f"{base_s3_path}{region}/"
        # region_specific_local_vocal_path = f"/tmp/{region}/"
        # region_specific_local_backing_path = f"/tmp/{region}/"
        # os.makedirs(region_specific_local_vocal_path, exist_ok=True)

        # # List of region-specific files (example: RomaniaTrack1MIDI.MID, RomaniaTrack2MIDI.MID)
        # region_vocal_files = [f"vocal_track/{region.capitalize()}Track1MIDI.mid", 
        #                       f"vocal_track/{region.capitalize()}Track2MIDI.mid", 
        #                       f"vocal_track/{region.capitalize()}Track3MIDI.mid", 
        #                       f"vocal_track/{region.capitalize()}Track4MIDI.mid", 
        #                       f"vocal_track/{region.capitalize()}Track5MIDI.mid",
        #                       f"vocal_track/{region.capitalize()}Track6MIDI.mid",
        #                       f"vocal_track/{region.capitalize()}Track7MIDI.mid",
        #                       f"vocal_track/{region.capitalize()}Track8MIDI.mid",
        #                       f"vocal_track/{region.capitalize()}Track9MIDI.mid",
        #                       f"vocal_track/{region.capitalize()}Track10MIDI.mid"
                              
        #                       ]  # Add or dynamically fetch file names if needed
        # region_backing_files = [f"backing_track/{region.capitalize()}Track1ChordMIDI.mid", 
        #                         f"backing_track/{region.capitalize()}Track2ChordMIDI.mid", 
        #                         f"backing_track/{region.capitalize()}Track3ChordMIDI.mid", 
        #                         f"backing_track/{region.capitalize()}Track4ChordMIDI.mid", 
        #                         f"backing_track/{region.capitalize()}Track5ChordMIDI.mid", 
        #                         f"backing_track/{region.capitalize()}Track6ChordMIDI.mid",
        #                         f"backing_track/{region.capitalize()}Track7ChordMIDI.mid", 
        #                         f"backing_track/{region.capitalize()}Track8ChordMIDI.mid", 
        #                         f"backing_track/{region.capitalize()}Track9ChordMIDI.mid",
        #                         f"backing_track/{region.capitalize()}Track10ChordMIDI.mid"
        #                        ]
        # # Download region-specific files
        # for file_name in region_vocal_files:
        #     s3_file_path = f"{region_specific_s3_path}{file_name}"
        #     local_file_path = os.path.join(region_specific_local_vocal_path, file_name)
            
        #     print(f"Downloading {s3_file_path} to {local_file_path}...")
        #     download_file_from_s3(BUCKET_NAME, s3_file_path, local_file_path)  # Replace with your S3 file download function
        #     print(f"Finished downloading {file_name}")
            
        # for file_name in region_backing_files:
        #     s3_file_path = f"{region_specific_s3_path}{file_name}"
        #     local_file_path = os.path.join(region_specific_local_backing_path, file_name)
            
        #     print(f"Downloading {s3_file_path} to {local_file_path}...")
        #     download_file_from_s3(BUCKET_NAME, s3_file_path, local_file_path)  # Replace with your S3 file download function
        #     print(f"Finished downloading {file_name}")
        
        # download_folder_from_s3(BUCKET_NAME, "Singers/", "/tmp/OpenUtau/Singers/", "")
        # Process each record
        for record in event['Records']:
            logger.info("Processing record: %s", record)
            body = json.loads(record['body'])
            logger.info("Body: %s", body)
            receipt_handle = record['receiptHandle']
            song_id = body.get("songID")
            
            try:
                # Parsing SQS message

                # OU_FINAL_FILENAME = f"song_{song_id}_vocals"
                # OU_INFERENCE_LOCAL_EXPORT_PATH = os.path.join(OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH, f"{OU_FINAL_FILENAME}.wav")
                
                notify_system_api(song_id, "utau_inference", "start", None, None)

                process_message(body)
                
                notify_system_api(song_id, "utau_inference", "end", f"{OU_FINAL_FILENAME}.wav", None, receipt_handle)

                

            except Exception as e:
                logger.error(f"Error processing record for song_id {song_id}: {e}")
                notify_system_api(song_id, "utau_inference", "err", None, e, None)

    except Exception as e:
        # This happened outside of Records array so cannot use systemAPI as it is 
        # NOT bound to any single songID
        logger.error(f"Critical error in lambda_handler: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
    
    finally:
        return {
        "statusCode": 200,
        "body": json.dumps({"message": "Processing completed successfully."})
    }
                
                
# DUMMY PAYLOAD FOR LOCAL TESTING
payload = {
            "Records": [
                {
                    "messageId": "unique-message-id",
                    "receiptHandle": "MessageReceiptHandle",
                    "body": json.dumps({"fileName": None, "songID": 107, "name": "David", "reason": "Supportive"}),
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

def run_openutau(project_name, export_wav_path, song_id):
    
    start_time = time.time()
    p = False
    song_log_file = f'/tmp/Logs/song_{song_id}_utaulogs.log'
    os.makedirs(os.path.dirname(song_log_file), exist_ok=True)
    song_logger = logging.getLogger(f'song_logger_{song_id}')
    song_handler = logging.FileHandler(song_log_file)
    song_handler.setLevel(logging.INFO)
    song_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    song_handler.setFormatter(song_format)
    song_logger.addHandler(song_handler)
    song_logger.propagate = False  # Prevents logging to propagate to root logger
    phonemizer = ""
    region = os.getenv('REGION_PROD')
    if region.lower() == "germany":
        phonemizer = "OpenUtau.Core.DiffSinger.DiffSingerGermanPhonemizer"
    elif region.lower() == "romania":
        phonemizer = "OpenUtau.Core.DiffSinger.DiffSingerRomanianPhonemizer"
    
    
    
    try:
        print("Running OpenUtau")

            
            
        process = subprocess.Popen(
            ["./OpenUtau", "--init"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        print("Subprocess started...")
        
        
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
                if output == '\n':
                    song_logger.info(accumulated_output.strip())
                    accumulated_output = ""
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
                    print(f"Detected '> ' prompt; sending '--import --midi {OU_INFERENCE_LOCAL_MIDI_PATH}'")
                    process.stdin.write(f"--import --midi {OU_INFERENCE_LOCAL_MIDI_PATH}\n")
                    process.stdin.flush()
                    midi_imported = True  # Set flag to avoid re-sending MIDI import
                    accumulated_output = ""  # Clear accumulated output
                # Send lyrics import command after MIDI import is complete
                elif '> ' in accumulated_output and midi_imported and not lyrics_imported:
                    print(f"Detected '> ' prompt; sending '--lyrics {OU_INFERENCE_LOCAL_LYRICS_PATH}'")
                    process.stdin.write(f"--lyrics {OU_INFERENCE_LOCAL_LYRICS_PATH}\n")
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
                    print(f"Detected singer selection prompt; entering '{OU_SINGER_NUMBER}'")
                    process.stdin.write(f"{OU_SINGER_NUMBER}\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # Respond to phonemizer selection prompt
                elif "Enter the phonemizer name to apply:" in accumulated_output:
                    print("Detected phonemizer selection prompt; entering 'OpenUtau.Core.DiffSinger.DiffSingerEnglishPhonemizer'")
                    # OpenUtau.Core.DiffSinger.DiffSingerGermanPhonemizer
                    # OpenUtau.Core.DiffSinger.DiffSingerRomanianPhonemizer
                    # OpenUtau.Core.DiffSinger.DiffSingerEnglishPhonemizer
                    process.stdin.write(f"{phonemizer}\n")
                    process.stdin.flush()
                    accumulated_output = ""  # Clear accumulated output
                # elif "> " in accumulated_output and not pitch_processing:
                #     print("Detected '> ' prompt; Sending '--process --pitch'")
                #     time.sleep(2)
                #     # process.stdin.write("--process --pitch\n")
                #     # process.stdin.flush()
                #     time.sleep(2)
                #     accumulated_output = ""
                #     # breakpoint()

                # elif "Select a part to process:" in accumulated_output and not pitch_processing:
                #     print("Detected Part selection prompt; entering '1'")
                #     process.stdin.write("1\n")
                #     process.stdin.flush()
                #     pitch_processing = True
                #     accumulated_output = ""
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
                    time.sleep(5)
                     
                # elif p and export_fully_completed:
                #     print("[red]Detected '> ' prompt; sending '--exit'[/red]")
                #     # process.stdin.write(OU_INFERENCE_LOCAL_EXPORT_PATH)
                #     # process.stdin.flush()
                #     p = False
                
                elif p and export_fully_completed and '> ' in accumulated_output:
                    print("[red]Detected '> ' prompt; sending '--exit'[/red]")
                    time.sleep(5)
                    p = False
                    
                elif "Project has been successfully exported to WAV" in accumulated_output:
                    return                    
                    
            # Check if process has ended
            if process.poll() is not None:
                print("Process ended.")
                break
    except Exception as e:
        print("Error encountered:", e)
        notify_system_api(song_id, "utau_inference", "error", None, str(e), None) 
    finally:
        if process:
            process.terminate()  # Ensure the process is terminated  

    # Calculate and print the time taken
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")
    logger.info(f"Total time taken: {total_time:.2f} seconds")
            
# LOCAL TESTING  
# if IS_LAMBDA_ENV:
    # response = lambda_handler(payload, None)
    # print(response)
# if __name__ == "__main__":
        # logger.info("Starting SQS polling on EC2")
        
# response = lambda_handler(payload, None)
# print(response)
# poll_sqs() #poll_sqs(sqs_client, SQS_QUEUE_URL, process_message)
