from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()
region = os.getenv("REGION_PROD")
IS_LAMBDA_ENV = os.getenv("AWS_LAMBDA_FUNCTION_NAME")
VOICE_COLOR_OPTIONS = ""
if IS_LAMBDA_ENV != None:
    IS_LAMBDA_ENV = True
else:
    IS_LAMBDA_ENV = False

bpm_data = {}
bpm_data['germany'] = {}
bpm_data['germany'][1] = 120 
bpm_data['germany'][2] = 120
bpm_data['germany'][3] = 108 
bpm_data['germany'][4] = 100
bpm_data['germany'][5] = 98
bpm_data['germany'][6] = 90
bpm_data['germany'][7] = 96
bpm_data['germany'][8] = 104
bpm_data['germany'][9] = 106
bpm_data['germany'][10] = 84
bpm_data['romania'] = {}
bpm_data['romania'][1] = 115
bpm_data['romania'][2] = 90
bpm_data['romania'][3] = 100
bpm_data['romania'][4] = 100
bpm_data['romania'][5] = 120
bpm_data['romania'][6] = 120
bpm_data['romania'][7] = 105
bpm_data['romania'][8] = 100
bpm_data['romania'][9] = 94
bpm_data['romania'][10] = 100
bpm_data['mexico'] = {}
bpm_data['mexico'][1] = 99
bpm_data['mexico'][2] = 97
bpm_data['mexico'][3] = 103
bpm_data['greece'] = {}
bpm_data['greece'][1] = 134 # pop
bpm_data['greece'][2] = 143 # ballad
bpm_data['greece'][3] = 130 # folk
bpm_data['slovakia'] = {}
bpm_data['slovakia'][1] = 120
bpm_data['slovakia'][2] = 90
bpm_data['slovakia'][3] = 95
bpm_data['slovakia'][4] = 97
bpm_data['slovakia'][5] = 100
bpm_data['slovakia'][6] = 110
bpm_data['slovakia'][7] = 122
bpm_data['slovakia'][8] = 102
bpm_data['slovakia'][9] = 116
bpm_data['slovakia'][10] = 105
bpm_data['czechia'] = {}
bpm_data['czechia'][1] = 120
bpm_data['czechia'][2] = 90
bpm_data['czechia'][3] = 95
bpm_data['czechia'][4] = 97
bpm_data['czechia'][5] = 100
bpm_data['czechia'][6] = 110
bpm_data['czechia'][7] = 112
bpm_data['czechia'][8] = 102
bpm_data['czechia'][9] = 116
bpm_data['czechia'][10] = 105
bpm_data['hungary'] = {}
bpm_data['hungary'][1] = 80
bpm_data['hungary'][2] = 116
bpm_data['hungary'][3] = 85
bpm_data['hungary'][4] = 90
bpm_data['hungary'][5] = 120
bpm_data['hungary'][6] = 84
bpm_data['hungary'][7] = 120
bpm_data['hungary'][8] = 88
bpm_data['hungary'][9] = 98
bpm_data['hungary'][10] = 96

note_count = {}
note_count['slovakia']= {}
note_count['slovakia'][4] = [11, 11, 11, 11, 12, 12, 9, 13, 14, 12]
note_count['slovakia'][5] = [11, 11, 12, 11, 12, 15, 11, 10, 14, 10]


note_count['czechia']= {}
note_count['czechia'][4] = [11, 11, 11, 11, 12, 12, 9, 13, 14, 12]
note_count['czechia'][5] = [11, 11, 12, 11, 12, 15, 11, 10, 14, 10]

# legato, arpeggios, falcetto 

lyrics_timing_map = {}
lyrics_timing_map["slovakia"] = {}
lyrics_timing_map["slovakia"][4] = [
        (4.9, 4.3),
        (9.5, 4.6),
        (14.4, 5.1),
        (19.7, 4.7),
        (24.7, 4.3),
        (29.3, 34.2-29.3),
        (34.6, 38.9-34.6),
        (39.2, 43.9-39.2),
        (44.4, 48.9 - 44.4),
        (49.1, 54.4-49.1)
    ]
lyrics_timing_map["slovakia"][5] = [
        (10.5, 15.0-10.5),
        (15.6, 19.8-15.6),
        (20.1, 24.6-20.1),
        (25.2, 29.4-25.2),
        (30.0, 4.3),
        (34.5, 39.0-34.5),
        (39.6, 43.5-39.6),
        (44.1, 48.9-44.1),
        (49.2, 53.5 - 49.2),
        (54.0, 58.8-54.0)
    ]


lyrics_timing_map["czechia"] = {}
lyrics_timing_map["czechia"][4] = [
        (4.9, 4.3),
        (9.5, 4.6),
        (14.4, 5.1),
        (19.7, 4.7),
        (24.7, 4.3),
        (29.3, 34.2-29.3),
        (34.6, 38.9-34.6),
        (39.2, 43.9-39.2),
        (44.4, 48.9 - 44.4),
        (49.1, 54.4-49.1)
    ]
lyrics_timing_map["czechia"][5] = [
        (10.5, 15.0-10.5),
        (15.6, 19.8-15.6),
        (20.1, 24.6-20.1),
        (25.2, 29.4-25.2),
        (30.0, 4.3),
        (34.5, 39.0-34.5),
        (39.6, 43.5-39.6),
        (44.1, 48.9-44.1),
        (49.2, 53.5 - 49.2),
        (54.0, 58.8-54.0)
    ]


@dataclass
class Config:
    BUCKET_NAME: str
    REGION_NAME: str
    is_lambda_env: bool
    SQS_QUEUE_URL: str
    OU_INFERENCE_LOCAL_MIDI_PATH: str
    OU_INFERENCE_LOCAL_LYRICS_PATH: str
    OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH: str
    OU_SINGER_NUMBER: str
    OU_FINAL_FILENAME: str
    OU_INFERENCE_LOCAL_EXPORT_PATH: str
    OU_INFERENCE_LOCAL_USTX_PATH: str
    OU_LYRICS_JSON_PATH: str
    OU_PROCESS_LOGS: str
    SECTIONAL_MIDI_FOLDER: str
    ADJUSTED_SECTIONAL_MIDI_FOLDER: str
    OUTPUT_FOLDER: str
    GREECE_TRACK2_SECTIONS: str
    VOICE_COLOR_OPTIONS: str

def initialize_config():
    is_lambda_env = IS_LAMBDA_ENV  # Modify this as needed for your environment check
    ou_singer_num = "1"
    
    if region == "australia":
        VOICE_COLOR_OPTIONS = "1"
    elif region == "czechia":
        VOICE_COLOR_OPTIONS = "0"
    elif region == "germany":
        VOICE_COLOR_OPTIONS = "2"
    elif region == "greece":
        VOICE_COLOR_OPTIONS = "3"
    elif region == "hungary":
        VOICE_COLOR_OPTIONS = "4"
    elif region == "romania":
        VOICE_COLOR_OPTIONS = "5"
    elif region == "mexico":
        VOICE_COLOR_OPTIONS = "7"
    elif region == "slovakia":
        VOICE_COLOR_OPTIONS = "6"
    
    
    # UNCOMMENT WHEN ALL MODELS ARE 
    # PLACED IN SINGLE LAMBDA
    
    # if region == "australia":
    #     ou_singer_num = "1"
    # elif region == "czechia":
    #     ou_singer_num = "2"
    # elif region == "germany":
    #     ou_singer_num = "3"
    # elif region == "hungary":
    #     ou_singer_num = "4"
    # elif region == "romania":
    #     ou_singer_num = "5"
    # elif region == "mexico":
    #     ou_singer_num = "6"
    
    config = Config(
        VOICE_COLOR_OPTIONS,
        BUCKET_NAME=os.getenv("BUCKET_NAME"),
        REGION_NAME=os.getenv("REGION_NAME"),
        is_lambda_env=IS_LAMBDA_ENV,
        SQS_QUEUE_URL=os.getenv("SQS_QUEUE_URL"),
        OU_INFERENCE_LOCAL_MIDI_PATH="/tmp/midi.mid" if is_lambda_env else "tmp/midi.mid",
        OU_INFERENCE_LOCAL_LYRICS_PATH="/tmp/lyrics.txt" if is_lambda_env else "tmp/lyrics.txt",
        OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH="/tmp/" if is_lambda_env else "tmp/",
        OU_SINGER_NUMBER=ou_singer_num,
        OU_FINAL_FILENAME="",
        OU_INFERENCE_LOCAL_EXPORT_PATH="",
        OU_INFERENCE_LOCAL_USTX_PATH="",
        OU_LYRICS_JSON_PATH="/tmp/lyrics.json" if is_lambda_env else "tmp/lyrics.json",
        OU_PROCESS_LOGS="/tmp/Logs/openutau_process.log" if is_lambda_env else "tmp/Logs/openutau_process.log",
        SECTIONAL_MIDI_FOLDER="/tmp/outputs/sections" if is_lambda_env else "tmp/outputs/sections",
        ADJUSTED_SECTIONAL_MIDI_FOLDER="/tmp/outputs/adjusted_sections" if is_lambda_env else "tmp/outputs/adjusted_sections",
        OUTPUT_FOLDER="/tmp/outputs" if is_lambda_env else "tmp/outputs",
        GREECE_TRACK2_SECTIONS="greek_track1_sections",
    )
    
    # Return initialized config
    return config
