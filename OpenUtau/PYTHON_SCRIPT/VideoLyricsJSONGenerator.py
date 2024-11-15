from openai import OpenAI
import re
import json
import helpers
import openai
import boto3
import botocore
import os
from botocore.exceptions import ClientError
from helpers import download_file_from_s3, wait_for_file

REGION_NAME = os.getenv('REGION_NAME')
BUCKET_NAME = os.getenv('BUCKET_NAME')

s3_client = boto3.client('s3', region_name=REGION_NAME)

SYSTEM_PROMPT = """"""


def get_system_prompt(name, reason):
    
    if wait_for_file(BUCKET_NAME, "system_prompt.txt", s3_client):
        download_file_from_s3(BUCKET_NAME, "system_prompt.txt", "/tmp/system_prompt.txt")
        
    try:
        with open("/tmp/system_prompt.txt", "r") as file:
            SYSTEM_PROMPT = file.read()
            

        # Print the content (optional, for debugging purposes)
        # print("Content of system_prompt.txt:")
        # print(SYSTEM_PROMPT)

    except FileNotFoundError:
        print("The file /tmp/system_prompt.txt was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        
    SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{name}", name).replace("{reason}", reason)
            
    return SYSTEM_PROMPT

class LyricsJSONAndTextGenerator:
    def __init__(self, api_key, bpm=100, time_signature=4, initial_offset=0.5):
        self.client = OpenAI(api_key=api_key)
        self.bpm = bpm
        self.time_signature = time_signature
        self.initial_offset = initial_offset

    def get_bar_duration(self):
        return round((60 / self.bpm) * self.time_signature, 2)

    def process_lyrics(self, lyrics):
        sections = re.split(r"(Verse|Chorus|Bridge|Intro|Outro):", lyrics)
        structured_lyrics = {}

        for i in range(1, len(sections), 2):
            section_name = sections[i].strip()
            lines = sections[i + 1].strip().splitlines()
            structured_lyrics[section_name] = [line.strip() for line in lines if line.strip()]

        return structured_lyrics

    def format_json_structure(self, lyrics_structure):
        bar_duration = self.get_bar_duration()
        current_time = self.initial_offset
        formatted_output = []

        for section, lines in lyrics_structure.items():
            for line in lines:
                json_entry = {
                    "text": line,
                    "start_time": round(current_time, 2),
                    "duration": bar_duration,
                    "num_syllables": count_syllables_in_line(line)
                }
                formatted_output.append(json_entry)
                current_time += bar_duration

        return formatted_output

    def request_formatted_json(self, lyrics_content):
        prompt = (
            "Convert the following lyrics into a compact JSON format where each entry includes the line of text, start_time, and duration. "
            "Assume a BPM of 94, 4 beats per bar, and start times increase by duration. Provide only the JSON in compact form: \n\n"
            f"Lyrics:\n{lyrics_content}"
            f""
        )

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        return response.choices[0].message.content.strip()

    def generate_response(self, lyrics_content, gpt_usage=True):
        if gpt_usage:
            formatted_json = self.request_formatted_json(lyrics_content)
        else:
            lyrics_structure = self.process_lyrics(lyrics_content)
            formatted_json = json.dumps(
                self.format_json_structure(lyrics_structure),
                indent=None,  # Compact without newlines
                separators=(",", ":"),
                ensure_ascii=False
            )

        # Return both the structured JSON and the original lyrics
        return {
            "json": formatted_json,
            "lyrics": lyrics_content
        }

class VideoLyricsJSONGenerator:
    def __init__(self, bpm=94, time_signature=4, start_offset=5.106):
        self.bpm = bpm
        self.time_signature = time_signature
        self.start_offset = start_offset

    def calculate_duration(self):
        return round((60 / self.bpm) * self.time_signature, 2)

    def parse_lyrics(self, lyrics):
        sections = re.split(r"(Verse|Chorus|Bridge|Outro):", lyrics)
        lyrics_dict = {}

        for i in range(1, len(sections), 2):
            section = sections[i].strip()
            lines = sections[i + 1].strip().splitlines()
            lyrics_dict[section] = [line.strip() for line in lines if line.strip()]
        
        return lyrics_dict

    def structure_lyrics_json(self, lyrics):
        print("Structuring Lyrics JSON")
        bar_duration = self.calculate_duration()
        current_start_time = self.start_offset
        results = []

        for line in lyrics.splitlines():
            if line.strip():  # Skip empty lines
                entry = {
                    "line": line.strip(),
                    "startTime": round(current_start_time, 2),
                    "duration": bar_duration
                }
                results.append(entry)
                current_start_time += bar_duration  # Increment start time by the bar duration

        return results

    def generate_json_file(self, input_file_path, output_file_path):
        with open(input_file_path, 'r', encoding='utf-8') as file:
            lyrics = file.read()

        structured_lyrics = self.structure_lyrics_json(lyrics)

        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(structured_lyrics, outfile, ensure_ascii=False)

        print(f"Structured JSON saved to {output_file_path}")

# class VideoLyricsJSONGenerator:
#     def __init__(self, api_key, bpm=94, time_signature=4, start_offset=5.106):
#         self.client = OpenAI(api_key=api_key)
#         self.bpm = bpm
#         self.time_signature = time_signature
#         self.start_offset = start_offset

#     def calculate_duration(self):
#         return round((60 / self.bpm) * self.time_signature, 2)

#     def parse_lyrics(self, lyrics):
#         # Split lyrics into sections based on "Verse:", "Chorus:", etc.
#         sections = re.split(r"(Verse|Chorus|Bridge|Outro):", lyrics)
#         lyrics_dict = {}

#         for i in range(1, len(sections), 2):
#             section = sections[i].strip()  # Section name
#             lines = sections[i + 1].strip().splitlines()  # Lyrics lines in the section
#             lyrics_dict[section] = [line.strip() for line in lines if line.strip()]
        
#         return lyrics_dict

#     def structure_lyrics_json(self, lyrics_dict):
#         print ("Structuring Lyrics JSON")
        
#         bar_duration = self.calculate_duration()
#         current_start_time = self.start_offset
#         results = []

#         for section, lines in lyrics_dict.items():
#             for line in lines:
#                 entry = {
#                     "line": line,
#                     "startTime": round(current_start_time, 2),
#                     "duration": bar_duration,
#                     "num_syllables": count_syllables_in_line(line)
#                 }
#                 results.append(entry)
#                 current_start_time += bar_duration  # Increment start time by the bar duration
        
#         return results

#     def request_gpt_format(self, lyrics_text):
#         prompt = (
#             "Please convert the following lyrics into a structured JSON format with each line "
#             "containing the line text, startTime in seconds, and duration in seconds. "
#             "Assume a BPM of 94, 4 beats per bar, and increment start times based on duration. "
#             "Generate only the JSON and nothing else. Do not include the ```json part. Do not json format with newlines please. compact json. \n\n"
#             f"Lyrics:\n{lyrics_text}"
#         )

#         response = self.client.chat.completions.create(
#             model="gpt-4o",  # Use gpt-4o model as specified
#             messages=[{"role": "user", "content": prompt}],
#             temperature=1,
#             max_tokens=2048,
#             top_p=1,
#             frequency_penalty=0,
#             presence_penalty=0,
#             response_format={"type": "text"}  # Specifying response format
#         )

#         return response.choices[0].message.content


#     def generate_response(self, lyrics_text, use_gpt=True):
#         if use_gpt:
#             # Process using GPT for formatting
#             structured_lyrics = self.request_gpt_format(lyrics_text)
            
#             # Convert the GPT response to a JSON object
#             structured_lyrics = json.loads(structured_lyrics)
            
#             # Calculate the duration for each line based on the BPM and time signature
#             bar_duration = self.calculate_duration()
#             current_start_time = self.start_offset

#             for entry in structured_lyrics:
#                 entry["startTime"] = round(current_start_time, 2)
#                 entry["duration"] = bar_duration
#                 current_start_time += bar_duration
                
#             structured_lyrics = json.dumps(structured_lyrics, indent=2, ensure_ascii=True)
#         else:
#             # Process locally without GPT
#             lyrics_dict = self.parse_lyrics(lyrics_text)
#             # Clean up and structure JSON without extra whitespace or newlines
#             structured_lyrics = json.dumps(
#                 self.structure_lyrics_json(lyrics_dict), 
#                 indent=2,  # Adjusting to 2 spaces for better readability
#                 separators=(",", ": "),  # Compact format for lists and dicts
#                 ensure_ascii=False  # Allowing non-ASCII characters
#             )
#         return structured_lyrics
    
class AgentForLyricGeneration:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.client.api_key = api_key
        self.model = model

    def generate_similar_lyrics(self, original_lyrics):
        prompt = (
            "Generate new song lyrics that are similar in theme and structure to the following:\n"
            f"{original_lyrics}\n\n"
            "Ensure each line maintains the poetic style of the original."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        return response.choices[0].message.content.strip()

class AgentForLineAdjustment:
    def __init__(self, api_key, model="gpt-4o-mini"):
        """Initialize the agent with the API key and model."""
        self.client = OpenAI(api_key=api_key)
        self.client.api_key = api_key
        self.model = model

    def request_adjustment(self, line, action, context=""):
        """Query GPT to adjust a line with specific instructions."""
        prompt = (
            f"Here is a verse from a song for context:\n"
            f"{context}\n\n"
            f"Line that needs adjustment: \"{line}\"\n"
            f"Action needed: {action}\n\n"
            f"Please provide a new line that fits this context and follows the action."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        return response.choices[0].message.content.strip()
class LyricGPTAgent:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.client.api_key = api_key
        self.model = model

    def generate_lyrics(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": "You are a creative assistant who writes song lyrics."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def create_first_four_lines(self, name, reason):
        SYSTEM_PROMPT = get_system_prompt(name, reason)
        return (
           f"""SYSTEM PROMPT:{SYSTEM_PROMPT}

            USER PROMPT:
            
            "Write original song lyrics similar to the classic holiday song 'Jingle Bells'. Follow these rules:\n"
            "1. The song should have a playful and festive theme.\n"
            "2. The syllable structure should be maintained as follows:\n"
            "   - Line 1: 5 syllables\n"
            "   - Line 2: 7 syllables\n (This line technically starts two quarter notes before the bar), and should never contain only 6 syllables"
            "   - Line 3: 5 syllables or 7 syllables, never 6\n"
            "   - Line 4: 5 syllables, never 4\n"
            # "   - Line 5: 5 syllables, never 4\n"
            # "   - Line 6: 5 syllables, never 4\n"
            # "   - Line 7: 9 syllables\n"
            # "   - Line 8: 5 or 6 syllables\n"
            "3. The lyrics should evoke joy, togetherness, and a fun winter holiday spirit.\n"
            "4. Use simple language and keep the lyrics easy to remember and sing."
            "5. Generate only 4 lines of lyrics for the jingle"
            "6. Ensure the lyrics flow"
            "7. Ensure the syllable count is correct. This is extremely important. The project fails if this fails."
            "8. Ensure every line has more than 4 syllables and more than 4 words"
            "9. Print the number of syllables to the right of each line. Be accurate"
            "10. Don't generate anything other than the lyrics. This stuff will be blindly copied."
            """
        )
        
    def create_second_four_lines(self, lyrics):
        return (
            f"SYSTEM PROMPT:{SYSTEM_PROMPT}"
            "Generate 4 more lines to add to the previous lyrics: {lyrics}"
            "1. The song should have a playful and festive theme.\n"
            "2. The syllable structure should be maintained as follows:\n"
            "   - Line 5: 5 syllables, never 4\n"
            "   - Line 6: 5 syllables, never 4\n"
            "   - Line 7: 7 syllables\n"
            "   - Line 8: 5 syllables with ONLY monosyllabic words.\n"
            "3. The lyrics should evoke joy, togetherness, and a fun winter holiday spirit.\n"
            "4. Use simple language and keep the lyrics easy to remember and sing."
            "5. Generate only 4 lines of lyrics for the jingle"
            "6. Ensure the lyrics flow"
            "7. Ensure the syllable count is correct. This is extremely important. The project fails if this fails."
            "8. Ensure every line has more than 4 syllables and more than 4 words"
            "9. Print the number of syllables to the right of each line. Be accurate."
            "10. Don't mention the total syllable count. Only generate the lyrics. This text wil be blindly appended"
        )
        
    def create_a_verse(self, name, reason):
        SYSTEM_PROMPT = get_system_prompt(name, reason)
        return (
            f"SYSTEM PROMPT:{SYSTEM_PROMPT}"
            "Generate a verse with 8 lines that would fit the following verse:"
            "1. The song should have a playful and festive theme.\n"
            "2. The syllable structure should be maintained as follows:\n"
            "   - Line 1: 5 syllables\n"
            "   - Line 2: 7 syllables\n (This line technically starts two quarter notes before the bar), and should never contain only 6 syllables"
            "   - Line 3: 5 syllables or 7 syllables, never 6\n"
            "   - Line 4: 5 syllables, never 4\n"
            "   - Line 5: 5 syllables, never 4\n"
            "   - Line 6: 5 syllables, never 4\n"
            "   - Line 7: 7 syllables\n"
            "   - Line 8: 5 syllables\n"
            "3. Generate ONLY the lyrics and nothing else"
            "4. The song must clearly include the name and the reason in the lyrics."
        )

    def create_a_chorus(self, lyrics, reason):
        return (
            f"SYSTEM PROMPT:{SYSTEM_PROMPT}"
            "Generate a chorus with 8 lines that would fit the following verse: {lyrics}"
            "It must bring back emphasis on the reason: {reason}"
            "1. The song should have a playful and festive theme.\n"
            "2. The syllable structure should be maintained as follows:\n"
            "   - Line 1: Jingle Bells, Jingle Bells\n"
            "   - Line 2: Jingle all the way \n"
            # "   - Line 3: Oh what ___ ___ ___ ___ ___ (these are single syllables, 5 syllables or less ONLY!!!!)\n"
            "   - Line 3: Oh what fun it is to ride (these are single syllables, 6 syllables or less ONLY!!!!)\n"
            # "   - Line 4: _ _ _ _ _ (these are single syllables) \n"
            "   - Line 4: a one horse open sleigh (these are single syllables) \n"
            "   - Line 5: Jingle Bells, Jingle Bells\n"
            "   - Line 6: Jingle all the way\n"
            # "   - Line 7: Oh what _ _ _ _ _ (6 or 7 syllables are necessary) \n"
            # "   - Line 8: _ _ _ _ _ _ (5 syllables or less ONLY!!!!)\n"
            "   - Line 7: Oh what fun it is to ride (these are single syllables, 6 syllables or less ONLY!!!!)\n"
            "   - Line 8: a one horse open sleigh (these are single syllables) \n"
            "3. Generate ONLY the lyrics and nothing else"
            "4. Generate Jingle Bells, Jingle Bells for lines 1 and 5"
            "5. If you don't adhere to these rules, someone could get seriously injured. Don't let that happen."
            "6. The 'oh what' lines need to be related to the reason and this must be lyrically obvious."
            "7. When you can add 'the' to make a 4 syllable line a 5 syllable line, then do it."
        )

    def get_jingle_clone(self, name, reason):
        # prompt1 = self.create_first_four_lines(name, reason)
        # verse1 = self.generate_lyrics (prompt1)
        # prompt2 = self.create_second_four_lines(verse1)
        # verse2 = self.generate_lyrics (prompt2)
        
        # verse = verse1 + "\n" + verse2
        versePrompt = self.create_a_verse (name, reason)
        verse = self.generate_lyrics (versePrompt)
        chorus = self.generate_lyrics (self.create_a_chorus (verse, reason))
        
#         chorus = """Jingle Bells Jingle Bells
# Jingle all the way
# Oh what fun it is to ride a
# one horse open sleigh
# Jingle Bells Jingle Bells
# Jingle all the way
# Oh what joy it is to ride a 
# one horse open sleigh
#                 """
        jingle = verse + "\n" + chorus
        jingle = jingle.replace("'", "").replace(",", "")
        return jingle

class SyllableCountGPTAgent:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.client.api_key = api_key
        self.model = model

    def count_syllables_in_line(self, line):
        prompt = (
            "You will be given a line of lyrics. For each word, return the word followed by its syllable count "
            "in the format: word(syllable_count). Ensure each syllable count is accurate.\n\n"
            f"Lyrics line: \"{line}\"\n"
            "Return the formatted output in one line, like: word1(2) word2(1) word3(3) ..."
            "For the words Jingle Bells, assume the word Bells is always 2 syllables."
            "The 's at the end of a contracted word like 'it's' is not counted as a syllable."
            "John's is counted as 1 syllable. Chris's is counted as 2 syllables."
            "Be intelligent when assigning syllables."
            "'every' is 2 syllables. A contraction like you're is 1 syllable. you are is 2 syllables."
            "ious words like 'delicious' are 3 syllables. 'ious' is 1 syllable."
            "Elizabeth is 3 syllables as the a isn't pronounced in it."
            "today is 2 syllables. don't split today into to and day in output. today(2) is correct."
            "holiday is 3 syllables."
            "You are likely to break syllable counts with names and so you should try to be intelligent in correcting those disparities"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        formatted_output = response.choices[0].message.content.strip()

        return formatted_output

    def get_syllable_count_from_response(self, formatted_line):
        words_with_counts = re.findall(r'(\b\w+\b)\((\d+)\)', formatted_line)
        syllable_dict = {}
        for word, count in words_with_counts:
            if word not in syllable_dict:
                syllable_dict[word] = int(count)
            else:
                # Append a unique key for repeated words to ensure they're all counted
                duplicate_key = f"{word}_{formatted_line.count(word)}"
                syllable_dict[duplicate_key] = int(count)
        return syllable_dict


    def request_syllable_counts(self, lyrics):
        # Get syllable counts for each line in the lyrics
        total_counts = []
        formatted_lines = []
        for line in lyrics:
            formatted_line = self.count_syllables_in_line(line)
            formatted_lines.append(formatted_line)
            syllable_dict = self.get_syllable_count_from_response(formatted_line)
            print (f"Syllable Dict: {syllable_dict}")
            total_count = sum(syllable_dict.values())
            total_counts.append(total_count)
            print (f"Line: {line} has {total_count} syllables")
                        
        print ("Total Counts:", total_counts)
        print ("Formatted Lines:", formatted_lines)
        return total_counts, formatted_lines
