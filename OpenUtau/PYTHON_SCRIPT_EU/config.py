from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()
region = os.getenv("REGION_PROD")
IS_LAMBDA_ENV = os.getenv("AWS_LAMBDA_FUNCTION_NAME")
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
bpm_data['greece'][1] = 134
bpm_data['greece'][2] = 143
bpm_data['greece'][3] = 130
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
bpm_data['hungary'][3] = 170
bpm_data['hungary'][4] = 90
bpm_data['hungary'][5] = 120
bpm_data['hungary'][6] = 92
bpm_data['hungary'][7] = 120
bpm_data['hungary'][8] = 88
bpm_data['hungary'][9] = 98
bpm_data['hungary'][10] = 96


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

def initialize_config():
    is_lambda_env = IS_LAMBDA_ENV  # Modify this as needed for your environment check
    ou_singer_num = "1"
    
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
        OUTPUT_FOLDER="/tmp/outputs" if is_lambda_env else "tmp/outputs"
    )
    
    # Return initialized config
    return config
