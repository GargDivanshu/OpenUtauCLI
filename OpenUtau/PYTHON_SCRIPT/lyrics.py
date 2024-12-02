from datetime import timedelta
import os
import re
import json
from dotenv import load_dotenv
from VideoLyricsJSONGenerator import VideoLyricsJSONGenerator, LyricGPTAgent, SyllableCountGPTAgent
from helpers import count_syllables, count_syllables_in_line, writeJSONStringToFile
import requests
import time
import random


# Load environment variables from .env
load_dotenv()

# Load API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Set the OPENAI_API_KEY environment variable.")

from midi_lyrics_service import midimain
from utau_lyrics_service import utau_lyrics_main
LYRICS_API_URL = os.getenv("LYRICS_API_URL")

def notify_lyrics_json_upload(song_id, file_name):
    url = LYRICS_API_URL
    data = {
        "songID": song_id,
        "fileName": file_name
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print(f"Notification sent successfully. Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to notify the API: {e}")

def format_line_in_utau(line):
    """Format the line in UTAU format by adding + after multisyllabic words."""
    words = line.split()
    formatted_line = []
    for word in words:
        syllable_count = count_syllables(word)
        if syllable_count > 1:
            formatted_line.append(f"{word} {'+ ' * (syllable_count - 1)}".strip())
        else:
            formatted_line.append(word)
    return ' '.join(formatted_line)

# Initialize the syllable counting agent
syllable_agent = SyllableCountGPTAgent(api_key)

def count_syllables(word):
    """Get the syllable count for a single word using the GPT agent."""
    line = word.strip()
    formatted_line = syllable_agent.count_syllables_in_line(line)
    syllable_counts = syllable_agent.get_syllable_count_from_response(formatted_line)
    return syllable_counts.get(word.lower(), 1)  # Return syllable count or default to 1

def count_syllables_in_line(line, use_gpt=True):
    """Calculate the number of syllables in a line using the GPT agent."""
    if use_gpt:
        formatted_line = syllable_agent.count_syllables_in_line(line)
        syllable_counts = syllable_agent.get_syllable_count_from_response(formatted_line)
        return sum(syllable_counts.values())
    else:
        # You can keep an alternative method here for non-GPT fallback if needed
        pass

def analyze_lyrics_syllables(lyrics):
    """Analyze the number of syllables in each line using GPT and report if it matches the expected count."""
    report = []
    lines = lyrics.split('\n')
    for line in lines:
        if not line.strip():
            continue
        if '(' in line and ')' in line:
            try:
                words_part, syllable_count_str = line.rsplit('(', 1)
                syllable_count_str = syllable_count_str.strip(')').strip()
                if syllable_count_str.isdigit():
                    target_count = int(syllable_count_str)
                    actual_count = count_syllables_in_line(words_part.strip(), use_gpt=True)
                    report.append({
                        "line": words_part.strip(),
                        "target_count": target_count,
                        "actual_count": actual_count,
                        "is_correct": actual_count == target_count
                    })
            except Exception as e:
                print(f"Error processing line: \"{line}\". {e}")
                report.append({"line": line.strip(), "target_count": None, "actual_count": None, "is_correct": False})
        else:
            actual_count = count_syllables_in_line(line, use_gpt=True)
            report.append({
                "line": line.strip(),
                "target_count": None,
                "actual_count": actual_count,
                "is_correct": None
            })
    return report

def print_lyric_report(report):
    """Print a report indicating which lines have the correct number of syllables."""
    print("Lyric Syllable Count Report:")
    for entry in report:
        line = entry["line"]
        target_count = entry["target_count"]
        actual_count = entry["actual_count"]
        is_correct = entry["is_correct"]
        if target_count is not None:
            status = "Correct" if is_correct else "Incorrect"
            print(f"Line: \"{line}\" | Expected syllables: {target_count}, Actual syllables: {actual_count}, Status: {status}")
        else:
            print(f"Line: \"{line}\" | Actual syllables: {actual_count}")

def add_num_syllables_to_json(json_data, field_name):
    """Add a field to each JSON element with the syllable count and replace 'lineText' with 'line' if present."""
    for element in json_data:
        if "lineText" in element:
            element["line"] = element.pop("lineText")
        if "line" in element:
            num_syllables = count_syllables_in_line(element["line"], use_gpt=True)
            element[field_name] = num_syllables
    return json_data

def main_lyrics(name, reason):
    """Main function to generate, analyze, and save lyrics."""
    lyrics = ""
    # Initialize LyricGPTAgent
    print ("Initializing LyricGPTAgent")
    # agent = LyricGPTAgent(api_key)

    # Step 1: Generate lyrics
    # start = time.monotonic()
    # lyrics = agent.get_jingle_clone(name, reason)
    # lyrics = re.sub(r'\d+', '', lyrics)
    # lyrics = re.sub(r'\[.*?\]', '', lyrics)
    # lyrics = re.sub(r'\(.*?\)', '', lyrics)
    # lyrics = lyrics.replace("{name}", name).replace("{reason}", reason)
    # lyrics = lyrics.strip()


    # Save lyrics to a text file
    if "wonderful" in reason.lower():
        lyrics = f"""
        Bouncing through the day,
        with a smile so big and bright,
        {name} is the best,
        spreading great delight.
        A heart thats pure and true,
        you are the very best,
        There is nothing you karnt do,
        now lets all sing the rest.
        Jingle bells, jingle bells
        Jingle all the way,
        Oh what fun its to ride "in a"
        one horse open sleigh.
        Jingle bells, jingle bells
        Jingle all the way,
        hey {name}, have a
        happy holiday!
        """
    elif "supportive" in reason.lower(): 
        lyrics = f"""
        {name} brings the love, 
        you are always there, 
        Your kindness knows no baundz, 
        so too does your care.  
        When its feeling tough, 
        youre who we need the most,
        Thanks for the suhpote, 
        now lets all share a toast. 
        Jingle bells, jingle bells
        Jingle all the way, 
        Oh what fun its to ride "in a" 
        one horse open sleigh.
        Jingle bells, jingle bells
        Jingle all the way, 
        hey {name}, have a 
        happy holiday!
        """
    elif "caring" in reason.lower():
        lyrics = f"""
        {name} always near, 
        "with a" heart so full of care.
        You help us when we are down, 
        you truly are so rare. 
        You are the very best and 
        make everything alright. 
        Thanks for all your care, 
        now lets sing this one right.
        Jingle bells, jingle bells
        Jingle all the way, 
        Oh what fun its to ride "in a" 
        one horse open sleigh.
        Jingle bells, jingle bells
        Jingle all the way, 
        hey {name}, have a 
        happy holiday!
        """
    elif "teacher" in reason.lower():
        lyrics = f"""
        {name} you are the best, 
        you inspire all the way,
        You make learning fun, 
        and teach us every day. 
        You help build us up, 
        with a mind so sharp and wise, 
        Theres no teacher like you, 
        so heres a small surprise. 
        Jingle bells, jingle bells
        Jingle all the way, 
        Oh what fun its to ride "in a" 
        one horse open sleigh.
        Jingle bells, jingle bells
        Jingle all the way, 
        hey {name}, have a
        happy holiday!
        """
        
    elif "brightening" in reason.lower():
        lyrics = f"""
        {name} you are a star, 
        you chase the clouds away,
        Moments spent with you, 
        brighten up my day.
        Your kindness is a gift, 
        you stand out from the crowd. 
        So heres a card for you, 
        now sing it loud and proud.   
        Jingle bells, jingle bells
        Jingle all the way, 
        Oh what fun its to ride "in a" 
        one horse open sleigh.
        Jingle bells, jingle bells
        Jingle all the way, 
        hey {name}, have a 
        happy holiday!
        """
    
    lyrics = "\n".join(line.strip() for line in lyrics.strip().splitlines() if line.strip())
    with open("/tmp/lyrics_readable.txt", "w", encoding="utf-8") as file:
        file.write(lyrics)
        
    # end = time.monotonic()
    
    # print("Time taken to generate lyrics and write them to lyrics_readable:", timedelta(seconds=end-start))


    start = time.monotonic()
    # Step 2: Generate structured lyrics JSON using GPT
    
    # Create an instance of the VideoLyricsJSONGenerator
    json_agent = VideoLyricsJSONGenerator()

    # Read the lyrics from a file or provide them as input
    with open("/tmp/lyrics_readable.txt", "r", encoding="utf-8") as file:
        lyrics = file.read()

    # Generate structured JSON without using GPT
    structured_lyrics = json_agent.structure_lyrics_json(lyrics)

    # Define the path for the output file
    lyrics_file_path = "/tmp/lyrics.json"

    # Write the structured JSON to a file
    with open(lyrics_file_path, "w", encoding="utf-8") as outfile:
        json.dump(structured_lyrics, outfile, ensure_ascii=False)

    print(f"Structured JSON saved to {lyrics_file_path}")

    
    
    end = time.monotonic()
    print("Time taken to generate lyrics JSON:", timedelta(seconds=end-start))


    # start = time.monotonic()
    # # Step 3: Add syllable count to each JSON element
    with open(lyrics_file_path, 'r') as file:
        json_data = json.load(file)
    # updated_json_data = add_num_syllables_to_json(json_data, "num_syllables")
    # end = time.monotonic()
    # print("Time taken to add syllable count to JSON:", timedelta(seconds=end-start))
    
    updated_json_data = json_data
    for element in updated_json_data:
        if "lineText" in element:
            element["line"] = element.pop("lineText")
    # Save the updated JSON data back to the file
    with open(lyrics_file_path, 'w', encoding='utf-8') as file:
        json.dump(updated_json_data, file, indent=4)

    # # Step 4: Analyze syllables and print a report
    # start = time.monotonic()
    # syllable_report = analyze_lyrics_syllables(lyrics)
    # print_lyric_report(syllable_report)
    # end = time.monotonic()
    # print("Time taken to analyze syllables:", timedelta(seconds=end-start))

# Run the main_lyrics function with specified name and reason
def lyrics_process(name, reason):
    main_lyrics(name, reason) #saves lyrics to /tmp/lyrics_readable.txt and json to /tmp/lyrics.json
    
if __name__ == "__main__":
    lyrics_process("Tim", "brightening up my day")
