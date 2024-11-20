import json
import boto3
import botocore
import requests
from botocore.exceptions import ClientError
import time
import os
import logging
import re
import glob
import pretty_midi
import pyphen
from nltk.corpus import cmudict
from dotenv import load_dotenv

load_dotenv()
log_file = "tmp/Logs/openutau_process.log"
SYSTEM_API_URL = os.getenv("SYSTEM_API_URL")

# IS_LAMBDA_ENV 
IS_LAMBDA_ENV = False
# Configure logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()
BUCKET_NAME = os.getenv("BUCKET_NAME")
REGION_NAME = os.getenv("REGION_NAME")
# AWS & LAMBDA related keys
bucket_name = BUCKET_NAME
LAMBDA_STATIC_MIDI_FILE_PATH = "static/final.mid"
LAMBDA_STATIC_LYRICS_FILE_PATH = "static/lyrics.txt"

# Create AWS clients
s3_client = boto3.client('s3', region_name=REGION_NAME)
lambda_client = boto3.client('lambda', region_name=REGION_NAME)



def count_syllables(word):
    # Primary method: Check in the CMU Pronouncing Dictionary
    if word.lower() in d:
        return max([len([y for y in x if y[-1].isdigit()]) for x in d[word.lower()]])
    
    # Secondary method: Use Pyphen for fallback
    syllables = dic.inserted(word)
    count = syllables.count('-') + 1

    # Advanced rules for common English adjustments:
    # Handle silent 'e' at the end of words
    if word.endswith('e') and not word.endswith(('le', 'ue')) and count > 1:
        count -= 1
    
    # Handle diphthongs and vowel clusters more accurately
    if re.search(r'[aeiouy]{2,}', word):
        count = max(1, count)
    
    # Handle special suffixes like 'es', 'ed' when pronounced as one syllable
    if re.search(r'(es|ed)$', word) and count > 1:
        count -= 1
    
    # Correct for words ending in '-le'
    if word.endswith('le') and len(word) > 2 and not word[-3] in 'aeiou':
        count += 1

    return count

def count_syllables_in_line(line, use_cmu):
    # Clean and split the line into words
    words = re.findall(r'\b\w+\b', line)
    
    # Count syllables for each word
    syllable_count = sum(count_syllables(word, use_cmu) for word in words)

    return syllable_count

def clean_unicode_edge_case(json_data):
    """Replaces Unicode escape sequences in the 'line' fields with actual characters or replacements."""
    for entry in json_data:
        if "line" in entry:
            # Replace Unicode characters with their actual characters or custom replacements
            entry["line"] = entry["line"].replace("\u2019", "'")
    return json_data


def writeJSONStringToFile(jsonString, filePath):    
    # print (jsonString)
    # Parse the string as JSON
    parsed_json = json.loads(jsonString)

    clean_json = clean_unicode_edge_case(parsed_json)
    # Convert back to a formatted JSON string without escaped quotes
    clean_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)

    # Save the formatted JSON string to a file
    with open(filePath, 'w', encoding='utf-8') as f:
        f.write(clean_json)
        
def split_lyrics_into_sections(lyrics_text):
    # Use regex to split the input text into sections by markers like "Verse:", "Chorus:", etc.
    sections = re.split(r"(Verse|Chorus|Bridge|Intro|Outro):", lyrics_text)
    lyrics_dict = {}

    for i in range(1, len(sections), 2):
        section_name = sections[i].strip()  # Get section name (e.g., "Verse", "Chorus")
        section_lines = sections[i + 1].strip()  # Get the corresponding section content
        
        # Only add "Verse" and "Chorus" to the dictionary
        if section_name in ["Verse", "Chorus"]:
            lyrics_dict[section_name] = section_lines

    return lyrics_dict

import pretty_midi

def copy_instruments_within_segment(midi_data, start_time, end_time, bpm=120):
    new_midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    for instrument in midi_data.instruments:
        new_instrument = pretty_midi.Instrument(
            program=instrument.program, 
            is_drum=instrument.is_drum, 
            name=instrument.name
        )
        new_instrument.notes = [note for note in instrument.notes if start_time <= note.start < end_time]
        new_instrument.control_changes = [cc for cc in instrument.control_changes if start_time <= cc.time < end_time]
        new_instrument.pitch_bends = [pb for pb in instrument.pitch_bends if start_time <= pb.time < end_time]
        if new_instrument.notes:  # Only add instruments that have notes in the segment
            new_midi.instruments.append(new_instrument)
    return new_instrument, new_midi

# Function to calculate the duration of one bar in seconds
def calculate_bar_duration(bpm, time_signature=(4, 4)):
    beats_per_bar = time_signature[0]
    beat_duration = 60.0 / bpm  # Duration of one beat in seconds
    bar_duration = beats_per_bar * beat_duration  # Total duration of one bar in seconds
    return bar_duration

# Print the final summary
def print_final_summary(total_syllables, total_notes):
    print("\nFinal summary:")
    print(f"Total syllables in lyrics: {total_syllables}")
    print(f"Total notes in modified MIDI sections: {total_notes}")
    if total_notes == total_syllables:
        print("The total number of notes matches the total number of syllables.")
    else:
        print(f"The total number of notes does not match the total number of syllables. "
                f"Difference: {total_notes - total_syllables}")
        
        
# Load lyrics from a text file
def load_lyrics(file_path):
    with open(file_path, 'r') as file:
        lyrics = file.readlines()
    return [line.strip() for line in lyrics]


#section stuff

#calculate number of notes per section
def calculate_total_notes(sections_midi):
    return sum(len([note for instrument in section.instruments for note in instrument.notes]) for section in sections_midi)

def combine_midi_sections(sections_midi, bpm):
    # Create a new MIDI file to hold the combined sections
    final_midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)

    # Create a single instrument for all sections (e.g., Piano)
    combined_instrument = pretty_midi.Instrument(program=0, is_drum=False)  # Change `program` as needed
    for section in sections_midi:
        for instrument in section.instruments:
            combined_instrument.notes.extend(pretty_midi.Note(velocity=note.velocity, pitch=note.pitch + 12, start=note.start, end=note.end) for note in instrument.notes)
            combined_instrument.control_changes.extend(pretty_midi.ControlChange(number=cc.number, value=cc.value, time=cc.time) for cc in instrument.control_changes)
            combined_instrument.pitch_bends.extend(pretty_midi.PitchBend(pitch=pb.pitch, time=pb.time) for pb in instrument.pitch_bends)
            # Remove any notes below C0 (MIDI pitch 12)
            combined_instrument.notes = [note for note in combined_instrument.notes if note.pitch > 12]

    # Add the single combined instrument to the final MIDI file
    final_midi.instruments.append(combined_instrument)
    
    return final_midi


def get_last_end_time(section):
    """
    Returns the maximum end time among all notes in all instruments within a section.
    
    Args:
        section: An object that contains a list of instruments, where each instrument
                 has a list of notes with 'end' attributes.
    
    Returns:
        The maximum end time of all notes in the section.
    """
    return max(
        (note.end for instrument in section.instruments for note in instrument.notes),
        default=0
    )
    
    
# Copy instruments with notes within the segment range
def copy_instruments_within_range(midi_data, start_time, end_time, bpm):
    new_midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    for instrument in midi_data.instruments:
        new_instrument = pretty_midi.Instrument(program=instrument.program, is_drum=instrument.is_drum, name=instrument.name)
        new_instrument.notes = [note for note in instrument.notes if start_time <= note.start < end_time]
        new_instrument.control_changes = [cc for cc in instrument.control_changes if start_time <= cc.time < end_time]
        new_instrument.pitch_bends = [pb for pb in instrument.pitch_bends if start_time <= pb.time < end_time]
        
        if new_instrument.notes:  # Only add instruments that have notes in the segment
            new_midi.instruments.append(new_instrument)
        else:
            print (f"Skipping instrument {instrument.name} as it has no notes in the segment.")
    return new_midi


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


def download_folder_from_s3(bucket, folder_key, local_output_dir):
    """Download the specified folder from S3 to a local directory."""
    try:
        # Ensure the local output directory exists
        os.makedirs(local_output_dir, exist_ok=True)

        # List all objects with the folder prefix
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=folder_key)

        if 'Contents' not in response:
            logger.error(f"No files found in folder {folder_key} in bucket {bucket}.")
            return

        # Download each object in the folder
        for obj in response['Contents']:
            file_key = obj['Key']
            # Skip if the key represents the folder itself
            if file_key.endswith('/'):
                continue
            # Determine local file path
            local_file_path = os.path.join(local_output_dir, os.path.relpath(file_key, folder_key))
            # Ensure the subdirectories exist
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            # Download the file
            logger.info(f"Downloading {file_key} to {local_file_path}...")
            s3_client.download_file(bucket, file_key, local_file_path)
            logger.info(f"Downloaded {file_key} successfully.")
    except Exception as e:
        logger.error(f"Error downloading folder {folder_key}: {e}")
        raise e  # Raise exception to allow error handling



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
        except ClientError as e:
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
    tmp_dir = ''
    tmp_dir = "/tmp" if IS_LAMBDA_ENV else "/tmp"

    # Search for any .wav files in the tmp directory
    wav_files = glob.glob(os.path.join(tmp_dir, "*.wav"))
    
    if not wav_files:
        print(f"No WAV files found in {tmp_dir}.")
        return
    
        # Process each .wav file
    for file_path in wav_files:
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
            SYSTEM_API_URL,
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
        
        
# def log_and_expect(process, expected_prompt, stage_bar):
#     """
#     Utility to log the output of the process up until a specific prompt
#     and update the stage bar.
#     """
#     try:
#         process.expect(expected_prompt, timeout=30)  # Adjust timeout as needed
#         output = process.before.strip()  # Capture output before the prompt
#         if output:
#             logger.info(output)  # Log output to the file
#         stage_bar.update(1)  # Move to the next stage in tqdm
#     except expect.exceptions.TIMEOUT:
#         logger.error(f"Timeout waiting for prompt: {expected_prompt}")
#         raise
#     except expect.exceptions.EOF:
#         logger.error("Unexpected end of file reached.")
#         raise
