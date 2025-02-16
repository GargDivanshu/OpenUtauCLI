import pretty_midi
import os
import re
import boto3
import pyphen
import nltk
import pandas as pd
from carol_VideoLyricsJSONGenerator import SyllableCountGPTAgent
from helpers import calculate_bar_duration, download_folder_from_s3, print_final_summary,wait_for_file, download_file_from_s3, load_lyrics, calculate_total_notes, combine_midi_sections, get_last_end_time, copy_instruments_within_range
from carol_utau_lyrics_service import process_lyrics
import logging

REGION_NAME = os.getenv('REGION_NAME')
BUCKET_NAME = os.getenv("BUCKET_NAME")

s3_client = boto3.client('s3', region_name=REGION_NAME)
# Load lyrics and get syllable counts
def load_and_process_lyrics(filepath):
    lyrics = load_lyrics(filepath)
    syllable_count_agent = SyllableCountGPTAgent(api_key=os.getenv("OPENAI_API_KEY"))
    syllable_counts, formatted_lines = syllable_count_agent.request_syllable_counts(lyrics)
    
    # Add dummy syllable counts at the beginning
    syllable_counts.insert(0, 0)
    syllable_counts.insert(0, 0)
    
    final_formatted_string = ' '.join(formatted_lines)
    return lyrics, syllable_counts, formatted_lines, final_formatted_string

# Prepare MIDI note sequence
def get_note_sequence(note_sequence, note_mapping):
    return [note_mapping[note] for note in note_sequence]

# Split the MIDI file into sections and process each
def split_midi_file(input_file, output_folder, num_segments, bpm, syllable_counts, note_sequence_midi, note_duration):
    sections_info = []
    sections_midi = []
    midi_data = pretty_midi.PrettyMIDI(input_file, initial_tempo=bpm)
    total_duration = midi_data.get_end_time()
    segment_duration = total_duration / num_segments
    bar_duration = calculate_bar_duration(bpm)

    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, total_duration)
        new_midi = copy_instruments_within_range(midi_data, start_time, end_time, bpm)
        output_file = f'section_{i + 1}.mid'
        new_midi.write(os.path.join(output_folder, output_file))
        sections_midi.append(new_midi)

        note_count = len(new_midi.instruments[0].notes) if len(new_midi.instruments) > 0 else 0
        expected_syllables = syllable_counts[i] if i < len(syllable_counts) else 0
        diff = note_count - expected_syllables
        status = "matches" if diff == 0 else ("+notes" if diff < 0 else "-notes")

        if (i == 17):
            note_count = note_count - 1

        sections_info.append({
            "section_number": i + 1,
            "notes_count": note_count,
            "expected_syllables": expected_syllables,
            "difference": diff,
            "status": status
        })

        adjust_notes_in_section(i, sections_info, sections_midi, note_sequence_midi, note_duration, bar_duration)

    return sections_info, sections_midi

# Adjust notes in each section based on the syllable count difference
def adjust_notes_in_section(i, sections_info, sections_midi, note_sequence_midi, note_duration, bar_duration):
    if i == 0 or i >= len(sections_info) or sections_info[i]['status'] == "matches":
        return

    section_info = sections_info[i]
    if section_info['difference'] < 0 and i < 10:
        previous_section = sections_midi[i - 1]
        num_notes_to_add = abs(section_info['difference'])
        last_end_time = get_last_end_time(previous_section)
        end_of_bar_time = (last_end_time // bar_duration + 1) * bar_duration

        if last_end_time > 0:
            for j in range(num_notes_to_add):
                start_time = end_of_bar_time - (j + 1) * note_duration
                if start_time < last_end_time:
                    break

                note_pitch = note_sequence_midi[(i - 1) % len(note_sequence_midi)]
                if note_pitch >= 12:
                    new_note = pretty_midi.Note(
                        velocity=100,
                        pitch=note_pitch,
                        start=start_time,
                        end=start_time + note_duration
                    )
                    previous_section.instruments[0].notes.append(new_note)
                    logging.info(f"Added note with pitch {note_pitch} at start time {start_time:.2f} in section {i}.")

    elif section_info['difference'] > 0 and i < 10:  # If the section has more notes than needed
        current_section = sections_midi[i]
        num_notes_to_remove = section_info['difference']
        notes = current_section.instruments[0].notes

        if notes:
            bar_start_time = (notes[0].start // bar_duration) * bar_duration
            notes_to_remove = [note for note in notes if bar_start_time <= note.start < bar_start_time + bar_duration][:num_notes_to_remove]

            for note in notes_to_remove:
                current_section.instruments[0].notes.remove(note)
                logging.info(f"Removed note with pitch {note.pitch} at start time {note.start:.2f} in section {i}.")
                print ("Removing notes from section " + str(i))
                
    elif section_info['difference'] > 0 and i == 12 or i == 16:  # If the section has more notes than needed
        print ("Removing notes from section " + str(i))
        current_section = sections_midi[i]
        num_notes_to_remove = section_info['difference']
        notes = current_section.instruments[0].notes

        if notes:
            # Sort notes by start time in descending order to remove from right to left
            notes.sort(key=lambda note: note.start, reverse=True)
            
            bar_start_time = (notes[0].start // bar_duration) * bar_duration
            notes_to_remove = [note for note in notes if bar_start_time <= note.start < bar_start_time + bar_duration][:num_notes_to_remove]

            for note in notes_to_remove:
                current_section.instruments[0].notes.remove(note)
                logging.info(f"Removed note with pitch {note.pitch} at start time {note.start:.2f} in section {i}.")
                
    elif section_info['difference'] > 0 and i == 13 or i == 17:  # If the section has more notes than needed
        print ("Removing notes from section " + str(i))
        current_section = sections_midi[i]
        num_notes_to_remove = section_info['difference']
        notes = current_section.instruments[0].notes
        
        if i == 17:
             # Delete the last note
            if notes:
                 last_note = notes[-1]
                 current_section.instruments[0].notes.remove(last_note)
                 logging.info(f"Deleted last note with pitch {last_note.pitch} at start time {last_note.start:.2f} in section {i}.")
                 num_notes_to_remove -= 1

        if notes:
            bar_start_time = (notes[0].start // bar_duration) * bar_duration
            notes_to_remove = [note for note in notes if bar_start_time <= note.start < bar_start_time + bar_duration][:num_notes_to_remove]

            for note in notes_to_remove:
                current_section.instruments[0].notes.remove(note)
                logging.info(f"Removed note with pitch {note.pitch} at start time {note.start:.2f} in section {i}.")



# Create summary data for sections
def create_section_summary(sections_info):
    summary_data = [{
        "Section Number": section_info["section_number"],
        "Expected Syllables": section_info["expected_syllables"],
        "Actual Notes Count": section_info["notes_count"],
        "Difference": section_info["difference"],
        "Status": section_info["status"]
    } for section_info in sections_info]

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv('/tmp/section_summary.csv', index=False)
    return summary_df

# Main function to orchestrate the entire process
def midimain():
    lyrics, syllable_counts, formatted_lines, final_formatted_string = load_and_process_lyrics('/tmp/lyrics_readable.txt')
    note_sequence = ['A', 'A', 'B', 'A', 'A', 'A', 'B', 'D']
    note_mapping = {'A': 69 - 36, 'B': 71 - 36, 'D': 74 - 36}
    note_sequence_midi = get_note_sequence(note_sequence, note_mapping)
    
    bpm = 120
    note_duration = 0.25
    if wait_for_file(BUCKET_NAME, "bridgetnew.mid", s3_client):
        download_file_from_s3(BUCKET_NAME, "bridgetnew.mid", "/tmp/bridgetnew.mid")
        download_folder_from_s3(BUCKET_NAME, "midi_sections", "/tmp/midi_sections")
    trimmed_file = '/tmp/bridgetnew.mid'
    output_folder = '/tmp/midi_sections'
    
    bar_duration = calculate_bar_duration(bpm)

    sections_info, sections_midi = split_midi_file(trimmed_file, output_folder, num_segments=18, bpm=bpm, syllable_counts=syllable_counts, note_sequence_midi=note_sequence_midi, note_duration=note_duration)

    
    # Add notes to beats 5-8 of section 1 after the loop if sections_info[0]['difference'] < 0
    
    print ("There are " + str(len(sections_info)) + " sections.")
    print ("There are " + str(len(sections_midi[0].instruments)) + " instruments.")
    
    bar_start_time = 60.0 / bpm * 4.0;
    
    print("There are " + str(len(sections_info)) + " sections.")
    if sections_info[2]['difference'] < 0:
        instrument = pretty_midi.Instrument(program=0)  # Default program (e.g., piano)
        sections_midi[1].instruments.append(instrument)
        print("Adding notes to beats 8-5 of section 1.")
        num_notes = abs(sections_info[2]['difference'])
        section_1 = sections_midi[1].instruments[0]  # Access the MIDI object from sections_midi, not sections_info
        start_time_beat_8 = bar_start_time + (7 * note_duration)  # Start from beat 8

        [section_1.notes.append(pretty_midi.Note(
            velocity=100,
            pitch=note_sequence_midi[0 % len(note_sequence_midi)],
            start=start_time_beat_8 - (j * note_duration),
            end=start_time_beat_8 - (j * note_duration) + note_duration
        )) for j in range(num_notes) if start_time_beat_8 - (j * note_duration) >= bar_start_time + (4 * note_duration)]

    
    final_midi = combine_midi_sections(sections_midi, bpm)
    
    final_midi.write('/tmp/midi.mid')

    summary_df = create_section_summary(sections_info)
    print("Full Summary of Sections:")
    print(summary_df)

    total_difference = sum(section_info["difference"] for section_info in sections_info) - 1
    print(f"Total difference (sum of differences minus 1): {total_difference}")

    utau_lyrics = process_lyrics(final_formatted_string)
    print(utau_lyrics)

    return final_formatted_string, utau_lyrics

if __name__ == "__main__":
    midimain()

