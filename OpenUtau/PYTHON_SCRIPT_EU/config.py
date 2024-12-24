from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()
region = os.getenv("REGION_PROD")
# Define a dataclass for initialization
@dataclass
class Config:
    BUCKET_NAME: str
    REGION_NAME: str
    IS_LAMBDA_ENV: bool
    SQS_QUEUE_URL: str
    OU_INFERENCE_LOCAL_MIDI_PATH: str
    OU_INFERENCE_LOCAL_LYRICS_PATH: str
    OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH: str
    OU_SINGER_NUMBER: str
    OU_FINAL_FILENAME: str
    OU_INFERENCE_LOCAL_EXPORT_PATH: str
    OU_INFERENCE_LOCAL_USTX_PATH: str
    OU_LYRICS_JSON_PATH: str

def initialize_config():
    is_lambda_env = True  # Modify this as needed for your environment check
    ou_singer_num = "1"
    
    if region == "australia":
        ou_singer_num = "1"
    elif region == "germany":
        ou_singer_num = "2"
    elif region == "romania":
        ou_singer_num = "3"
    
    config = Config(
        BUCKET_NAME=os.getenv("BUCKET_NAME"),
        REGION_NAME=os.getenv("REGION_NAME"),
        IS_LAMBDA_ENV=is_lambda_env,
        SQS_QUEUE_URL=os.getenv("SQS_QUEUE_URL"),
        OU_INFERENCE_LOCAL_MIDI_PATH="/tmp/midi.mid" if is_lambda_env else "tmp/midi.mid",
        OU_INFERENCE_LOCAL_LYRICS_PATH="/tmp/lyrics.txt" if is_lambda_env else "tmp/lyrics.txt",
        OU_INFERENCE_LOCAL_PROJECT_SAVE_PATH="/tmp/" if is_lambda_env else "tmp/",
        OU_SINGER_NUMBER=ou_singer_num,
        OU_FINAL_FILENAME="",
        OU_INFERENCE_LOCAL_EXPORT_PATH="",
        OU_INFERENCE_LOCAL_USTX_PATH="",
        OU_LYRICS_JSON_PATH=""
    )
    
    # Return initialized config
    return config
