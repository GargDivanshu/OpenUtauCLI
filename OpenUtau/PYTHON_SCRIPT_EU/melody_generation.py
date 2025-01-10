#!/usr/bin/env python3
import pretty_midi
from pretty_midi import PrettyMIDI, note_name_to_number
import re
import os
from isobar import *
import logging
import time
import random
from collections import Counter, defaultdict
from dotenv import load_dotenv
from datetime import datetime
from music21 import *
import music21 as music21
import itertools
from helpers import save_markov_model, load_markov_model, midi_files, calculate_syllable_counts, ALL_SINGERS_RANGE, clamp, quantize_to_scale, quantize_note_durations
import shutil


load_dotenv()
# MODE = os.getenv("MODE")
# ACTIVE_SINGER = os.getenv("ACTIVE_SINGER")
# ACTIVE_SINGER_MIN_RANGE = 45
# ACTIVE_SINGER_MAX_RANGE = 75

# for singer in ALL_SINGERS_RANGE:
#     print(singer)
#     if singer["name"] == ACTIVE_SINGER:
#         ACTIVE_SINGER_MIN_RANGE = singer["min_range"]
#         print("min_range ", ACTIVE_SINGER_MIN_RANGE)
#         ACTIVE_SINGER_MAX_RANGE = singer["max_range"]
#         print("max_range ", ACTIVE_SINGER_MAX_RANGE)
note_markov = load_markov_model("./saved_pickle/note_markov.pkl")
dur_markov = load_markov_model("./saved_pickle/dur_markov.pkl")
amp_markov = load_markov_model("./saved_pickle/amp_markov.pkl")



# Example usage
chord_map = {
    # Major chords
    "Cmajor": set(['C', 'E', 'G']),
    "C#major": set(['C#', 'F', 'G#']),
    "Dmajor": set(['D', 'F#', 'A']),
    "D#major": set(['D#', 'G', 'A#']),
    "Emajor": set(['E', 'G#', 'B']),
    "Fmajor": set(['F', 'A', 'C']),
    "F#major": set(['F#', 'A#', 'C#']),
    "Gmajor": set(['G', 'B', 'D']),
    "G#major": set(['G#', 'C', 'D#']),
    "Amajor": set(['A', 'C#', 'E']),
    "A#major": set(['A#', 'D', 'F']),
    "Bmajor": set(['B', 'D#', 'F#']),

    # Minor chords
    "Cminor": set(['C', 'D#', 'G']),
    "C#minor": set(['C#', 'E', 'G#']),
    "Dminor": set(['D', 'F', 'A']),
    "D#minor": set(['D#', 'F#', 'A#']),
    "Eminor": set(['E', 'G', 'B']),
    "Fminor": set(['F', 'G#', 'C']),
    "F#minor": set(['F#', 'A', 'C#']),
    "Gminor": set(['G', 'A#', 'D']),
    "G#minor": set(['G#', 'B', 'D#']),
    "Aminor": set(['A', 'C', 'E']),
    "A#minor": set(['A#', 'C#', 'F']),
    "Bminor": set(['B', 'D', 'F#']),
}

def note_to_midi(note, chord_type):
    """
    Converts a chord root and type (major/minor) to MIDI note numbers.
    """
    root_pitch = pitch.Pitch(note[:-1])
    octave = int(note[-1])  # Extract octave from note
    root_midi = root_pitch.midi

    # Define intervals for major/minor triads
    if chord_type == "major":
        third = root_midi + 4
        fifth = root_midi + 7
    elif chord_type == "minor":
        third = root_midi + 3
        fifth = root_midi + 7
    else:
        raise ValueError(f"Unknown chord type: {chord_type}")

    # Assign proper octaves
    return [root_midi, third, fifth]


  
# def group_chord_progressions(json_data):
#     """
#     Group bars in pairs and extract unique chord progressions dynamically, 
#     including major and minor distinctions based on the scale.
#     """
#     from music21 import key, chord

#     bar_wise_chords = json_data["bar_wise_chords"]
#     detected_key = json_data["key"].name  # e.g., "A#"
#     detected_scale = "major"  # Placeholder: Assume "major"

#     # Analyze scale (major or minor)
#     if detected_scale.lower() == "major":
#         is_major_scale = True
#     else:
#         is_major_scale = False

#     # Group bars in pairs
#     grouped_chord_progressions = []
#     bars = sorted(bar_wise_chords.keys())
#     for i in range(0, len(bars), 2):
#         bar1 = bars[i]
#         bar2 = bars[i + 1] if i + 1 < len(bars) else None

#         # Combine chords from two bars
#         chords = bar_wise_chords[bar1]
#         if bar2:
#             chords.extend(bar_wise_chords[bar2])

#         # Simplify chords and include major/minor quality
#         simplified_chords = []
#         for c in chords:
#             root = c.split('-')[0]  # Get the root (e.g., "A#", "C")
#             quality = "major" if is_major_scale else "minor"
#             if "minor" in c:
#                 quality = "minor"
#             simplified_chords.append(f"{root}{quality}")

#         grouped_chord_progressions.append(simplified_chords)

#     # Deduplicate chord progressions
#     unique_progressions = []
#     for progression in grouped_chord_progressions:
#         if progression not in unique_progressions:
#             unique_progressions.append(progression)

#     return {
#         "detected_key": detected_key,
#         "detected_scale": detected_scale,
#         "unique_progressions": unique_progressions
#     }

    

# def replace_happy_progressions(json_data, target_list):
#     """
#     Replace hardcoded happy progressions with dynamically detected progressions,
#     including major and minor chord qualities.
#     """
#     chord_data = group_chord_progressions(json_data)
#     detected_key = chord_data["detected_key"]
#     detected_scale = chord_data["detected_scale"]
#     # detected_key = "F"
#     # detected_scale = "major"
#     unique_progressions = chord_data["unique_progressions"]

#     print("Detected Key:", detected_key)
#     print("Detected Scale:", detected_scale)
#     print("Unique Progressions:", unique_progressions)

#     # Replace target_list dynamically
#     target_list.clear()
#     for progression in unique_progressions:
#         midi_notes = []
#         for chord_name in progression:
#             root, quality = chord_name[:-5], chord_name[-5:]  # Split root and quality
#             chord_notes = get_chord_notes(root, quality)
#             midi_notes.append([note_to_midi(note) for note in chord_notes])
#         target_list.append(midi_notes)


# def get_chord_notes(root, quality):
#     """
#     Get the notes of a chord based on its root and quality.
#     """
#     if quality == "major":
#         return [root, f"{root}3", f"{root}5"]
#     elif quality == "minor":
#         return [root, f"{root}3-", f"{root}5"]
#     else:
#         return [root]

def group_bars_in_pairs(bar_data):
    """
    Groups bar-wise data into pairs: bar1-2, bar3-4, ...
    """
    paired_data = {}  # To store grouped pairs
    bars = sorted(bar_data.keys())  # Sort bar keys just in case

    for i in range(0, len(bars), 2):  # Iterate in steps of 2
        # Get current bar and next bar (if exists)
        bar_1 = bars[i]
        bar_2 = bars[i+1] if i+1 < len(bars) else None
        
        # Create a pair name, e.g., 'bar1-2'
        pair_key = f"bar{bar_1}-{bar_2}" if bar_2 else f"bar{bar_1}"
        
        # Merge data for both bars
        pair_data = {}
        pair_data['bar1'] = bar_data[bar_1]
        
        if bar_2:
            pair_data['bar2'] = bar_data[bar_2]
        
        # Store in paired_data
        paired_data[pair_key] = pair_data
    
    return paired_data

def map_unique_progressions(paired_data):
    """
    Map unique progressions across paired bars.
    Handles cases where a bar is unpaired (missing 'bar2').
    """
    progression_map = {}
    for pair, data in paired_data.items():
        # Skip pairs without both 'bar1' and 'bar2'
        if 'bar1' not in data or 'bar2' not in data:
            print(f"Skipping incomplete pair: {pair} -> {data}")
            continue

        progression = (tuple(data['bar1']), tuple(data['bar2']))

        if progression not in progression_map:
            progression_map[progression] = []

        progression_map[progression].append(pair)

    return progression_map


def combine_progressions(progression_map):
    """
    Combine progression tuples into unified progressions without sorting the order of chords.

    Parameters:
    - progression_map: A dictionary mapping progression tuples to bar pairs.

    Returns:
    - A dictionary combining progressions while preserving the original order.
    """
    combined_map = {}

    for progression, bars in progression_map.items():
        # Flatten the progression tuple while preserving the order
        combined_progression = tuple(sum(progression, ()))

        # Update the dictionary
        if combined_progression in combined_map:
            combined_map[combined_progression].extend(bars)
        else:
            combined_map[combined_progression] = bars.copy()

    return combined_map



def identify_vocal_activity(midi_file, bpm=120, velocity_threshold=10, duration_threshold=2):
    """
    Identify which bar pairs have genuine vocal activity based on cumulative note durations
    and exclude bar pairs with insufficient activity or late-starting notes.
    """
    from collections import defaultdict

    # Parse MIDI file
    music_data = converter.parse(midi_file)
    tempo = bpm  # Default tempo

    # Detect tempo
    for el in music_data.flatten().getElementsByClass(tempo):
        tempo = el.number
        break

    # Analyze bar-wise cumulative note durations
    bar_note_durations = defaultdict(float)
    bar_note_start_times = defaultdict(list)  # Track start times of notes in each bar

    for measure in music_data.parts[0].getElementsByClass(stream.Measure):  # Assuming first part is vocal
        bar_number = measure.number
        
        for elem in measure.notes:
            if elem.volume.velocity >= velocity_threshold:
                bar_note_durations[bar_number] += elem.quarterLength
                bar_note_start_times[bar_number].append(elem.offset)

    # Consolidate into bar pairs
    consolidated_activity = {"playing": [], "not_playing": []}
    max_bar = max(bar_note_durations.keys())  # Total number of bars

    for i in range(1, max_bar + 1, 2):  # Step through bars in pairs
        bar1_duration = bar_note_durations.get(i, 0)
        bar2_duration = bar_note_durations.get(i + 1, 0)
        bar1_starts = bar_note_start_times.get(i, [])
        bar2_starts = bar_note_start_times.get(i + 1, [])
        bar_pair = f"bar{i}-{i+1}"

        # Combined duration for the bar pair
        total_duration = bar1_duration + bar2_duration

        # Check for late starts in both bars
        late_start_bar1 = all(start > 6 for start in bar1_starts) if bar1_starts else True
        late_start_bar2 = all(start > 6 for start in bar2_starts) if bar2_starts else True

        # A bar pair is "playing" if total duration meets the threshold and neither starts late
        if total_duration >= duration_threshold and not (late_start_bar1 and late_start_bar2):
            consolidated_activity["playing"].append(bar_pair)
        else:
            consolidated_activity["not_playing"].append(bar_pair)

    # Handle the final bar if it's an odd number (trailing single bar)
    if max_bar % 2 != 0:
        final_bar = max_bar
        bar_pair = f"bar{final_bar}-{final_bar+1}"
        bar_duration = bar_note_durations.get(final_bar, 0)
        bar_starts = bar_note_start_times.get(final_bar, [])
        
        # Check late starts
        late_start = all(start > 6 for start in bar_starts) if bar_starts else True

        # Mark as playing or not
        if bar_duration >= duration_threshold and not late_start:
            consolidated_activity["playing"].append(bar_pair)
        else:
            consolidated_activity["not_playing"].append(bar_pair)

    return consolidated_activity


def filter_playing_progressions(combined_progressions, vocal_activity):
    """
    Filter the combined progressions to include only bar pairs that are in the 'playing' category.

    Parameters:
    - combined_progressions: A dictionary mapping unique chord progressions to bar pairs.
    - vocal_activity: A dictionary with 'playing' and 'not_playing' bar pairs.

    Returns:
    - A dictionary mapping unique chord progressions to their 'playing' bar pairs.
    """
    playing_bars = set(vocal_activity['playing'])  # Convert 'playing' list to a set for faster lookups
    filtered_progressions = {}

    for progression, bar_pairs in combined_progressions.items():
        # Filter bar pairs to include only those in the 'playing' category
        filtered_pairs = [bar for bar in bar_pairs if bar in playing_bars]
        if filtered_pairs:  # Only include progressions with at least one playing bar pair
            filtered_progressions[progression] = filtered_pairs

    return filtered_progressions


def preprocess_progression(progression):
    """
    Preprocess a progression tuple to convert it into the expected format for `progression_map`.

    Parameters:
    - progression: Tuple of chords (e.g., ('A#2-major triad', 'C3-major triad', 'F2-major triad')).

    Returns:
    - A tuple of chords in the format used in `progression_map`.
    """
    processed_progression = []
    for chord in progression:
        # Extract the root
        root = ""
        for char in chord:
            if char.isalpha() or char == '#':
                root += char
            else:
                break  # Stop at the first non-root character (e.g., '2', '-')
        
        # Determine the scale (major/minor)
        if "major" in chord:
            quality = "major"
        elif "minor" in chord:
            quality = "minor"
        else:
            raise ValueError(f"Unknown scale in chord: {chord}")
        
        # Append the processed chord
        processed_progression.append(f"{root}{quality}")
    return tuple(processed_progression)

def preprocess_progression_map(progression_map):
    """
    Preprocess the keys in progression_map to align them with processed progression format.
    """
    processed_map = {}
    for key, value in progression_map.items():
        processed_key = tuple(preprocess_progression(key))
        processed_map[processed_key] = value
    return processed_map


# Helper function to calculate cyclic distances
def cyclic_distance(current_midi, target_midi):
        upward_distance = (target_midi - current_midi) % 12
        downward_distance = (current_midi - target_midi) % 12
        return min(upward_distance, downward_distance)
    
    
def find_and_replace_large_gaps(notes, validation_report, chord_map, measure_number):
    """
    Adjust notes in a measure by aligning them closer to the average note.
    The best note minimizes the gap to the average while adhering to the chord's valid notes.

    Parameters:
    - notes: List of tuples (MIDI number, start time) for the measure.
    - validation_report: Dictionary mapping measure numbers to note details.
    - chord_map: Dictionary mapping chords to valid notes.
    - measure_number: Measure number (for logging/debugging).

    Returns:
    - Updated list of notes with adjustments.
    """
    from music21 import note
    import logging

    # logging.info(f"Processing measure {measure_number} to align notes closer to average")
    print(f"Processing measure {measure_number} to align notes closer to average")
    updated_notes = notes[:]

    # Calculate the average MIDI note for the measure
    all_midis = [midi for midi, _ in notes]
    avg_note = sum(all_midis) / len(all_midis)
    # logging.info(f"Measure {measure_number}: Average note: {avg_note:.2f}")
    print(f"Measure {measure_number}: Average note: {avg_note:.2f}")

    # Iterate over all notes in the measure
    for i, (current_note_midi, start_time) in enumerate(notes):
        # Find the chord for the current note from the validation report
        current_chord = None
        for val_note_name, _, chord in validation_report[measure_number]:
            if note.Note(current_note_midi).name == val_note_name:
                current_chord = chord.replace("Expected in ", "").replace("Valid in ", "").strip()
                break

        if not current_chord:
            # logging.error(f"No chord found for note {current_note_midi} in measure {measure_number}")
            print(f"ERROR: No chord found for note {current_note_midi} in measure {measure_number}")
            continue

        if current_chord not in chord_map:
            # logging.error(f"Chord {current_chord} not found in chord_map!")
            print(f"ERROR: Chord {current_chord} not found in chord_map!")
            continue

        # Determine valid notes from the chord
        valid_chord_notes = [
        n for chord_note in chord_map[current_chord]
        for n in [note.Note(chord_note).pitch.midi - 12, note.Note(chord_note).pitch.midi, note.Note(chord_note).pitch.midi + 12]
    ]

        # Select the best note: prioritize reducing the gap to the average
        best_note = None
        if valid_chord_notes:
            best_note = min(
                valid_chord_notes,
                key=lambda n: abs(n - avg_note)  # Minimize the distance to the average note
            )

        # If no valid chord notes, align to the left neighbor (or default to itself for the first note)
        if best_note is None:
            best_note = updated_notes[i - 1][0] if i > 0 else current_note_midi
            # logging.warning(
            #     f"Measure {measure_number}: No valid chord notes for {current_note_midi}. "
            #     f"Defaulting to left neighbor {best_note}."
            # )
            print(
                f"WARNING: Measure {measure_number}: No valid chord notes for {current_note_midi}. "
                f"Defaulting to left neighbor {best_note}."
            )

        # Update the note if it differs
        if best_note != current_note_midi:
            # logging.info(
            #     f"Measure {measure_number}: Replacing note {current_note_midi} with {best_note} "
            #     f"(closer to average {avg_note:.2f})"
            # )
            print(
                f"Measure {measure_number}: Replacing note {current_note_midi} with {best_note} "
                f"(closer to average {avg_note:.2f})"
            )
            updated_notes[i] = (best_note, start_time)

    return updated_notes


def correct_hanging_notes(notes):
    """
    Correct hanging notes by shifting them an octave if both neighbors are equidistant
    and the distance exceeds 6 semitones.

    Parameters:
    - notes: List of tuples (MIDI pitch, start time) representing notes in the measure.

    Returns:
    - List of corrected notes.
    """
    corrected_notes = notes.copy()  # Start with the original list of notes

    print("\nInitial notes:")
    for midi_pitch, start_time in corrected_notes:
        print(f"MIDI {midi_pitch}, Start time: {start_time}")

    for i in range(len(corrected_notes)):
        current_pitch, current_start = corrected_notes[i]
        print(f"\nProcessing note: MIDI {current_pitch}, Start time: {current_start}")

        # Skip edge notes (first and last) as they do not have two neighbors
        if i == 0 or i == len(corrected_notes) - 1:
            print("Skipping edge note (no two neighbors).")
            continue

        # Determine neighbors
        left_neighbor = corrected_notes[i - 1][0]
        right_neighbor = corrected_notes[i + 1][0]
        print(f"Left neighbor: MIDI {left_neighbor}, Right neighbor: MIDI {right_neighbor}")

        # Calculate distances to neighbors
        left_gap = abs(current_pitch - left_neighbor)
        right_gap = abs(current_pitch - right_neighbor)
        print(f"Gap with left neighbor: {left_gap} semitones, Gap with right neighbor: {right_gap} semitones")

        # Check for hanging note condition
        if left_gap > 6 and right_gap > 6 and left_gap == right_gap:
            print("Hanging note detected. Correcting...")
            shift = 12 * (-1 if current_pitch > left_neighbor else 1)  # Direction depends on neighbors
            new_pitch = current_pitch + shift
            print(f"Shifting note from MIDI {current_pitch} to {new_pitch} by {shift} semitones.")
            corrected_notes[i] = (new_pitch, current_start)
        else:
            print("Note is not a hanging note. No correction applied.")

    print("\nFinal corrected notes for the measure:")
    for midi_pitch, start_time in corrected_notes:
        print(f"MIDI {midi_pitch}, Start time: {start_time}")

    return corrected_notes


def octave_normalization_with_two_octaves(midi_file, target_octave1, target_octave2, output_file):
    """
    Normalize all notes in a MIDI file to the specified octaves while preserving the pitch class.
    - First 6 pitch classes (C, C#, D, D#, E, F) are normalized to target_octave1.
    - Next 6 pitch classes (F#, G, G#, A, A#, B) are normalized to target_octave2.
    Parameters:
    - midi_file: Path to the input MIDI file.
    - target_octave1: The target octave for the first 6 pitch classes.
    - target_octave2: The target octave for the next 6 pitch classes.
    - output_file: Path to save the normalized MIDI file.
    """
    print(f"Normalizing notes in {midi_file} to octaves {target_octave1} and {target_octave2}.")
    # Parse the MIDI file
    from music21 import converter, note
    midi_data = converter.parse(midi_file, format='midi')
    # Iterate over each measure and normalize notes
    for part in midi_data.parts:
        for measure in part.getElementsByClass('Measure'):
            for elem in measure.notes:
                if isinstance(elem, note.Note):
                    original_pitch = elem.pitch
                    pitch_class = original_pitch.pitchClass  # Get the pitch class (C=0, C#=1, ..., B=11)
                    # Assign to the appropriate octave based on pitch class
                    if pitch_class <= 5:  # C, C#, D, D#, E, F
                        normalized_pitch = (target_octave1 * 12) + pitch_class
                    else:  # F#, G, G#, A, A#, B
                        normalized_pitch = (target_octave2 * 12) + pitch_class
                    elem.pitch.midi = normalized_pitch
                    print(f"Note {original_pitch} normalized to {elem.pitch} in octaves {target_octave1}/{target_octave2}.")
    # Save the normalized MIDI file
    midi_data.write('midi', fp=output_file)
    print(f"Normalized MIDI saved to {output_file}.")
    
    

def octave_normalization(midi_file, target_octave, output_file):
    """
    Normalize all notes in a MIDI file to the specified octave while preserving the pitch class.

    Parameters:
    - midi_file: Path to the input MIDI file.
    - target_octave: The target octave to which all notes should be normalized.
    - output_file: Path to save the normalized MIDI file.
    """
    print(f"Normalizing notes in {midi_file} to octave {target_octave}.")
    
    # Parse the MIDI file
    midi_data = converter.parse(midi_file)
    
    # Iterate over each measure and normalize notes
    for part in midi_data.parts:
        for measure in part.getElementsByClass('Measure'):
            for elem in measure.notes:
                # if isinstance(elem, note.Note):
                    original_pitch = elem.pitch
                    pitch_class = original_pitch.pitchClass  # Get the pitch class (C=0, C#=1, ..., B=11)
                    normalized_pitch = (target_octave * 12) + pitch_class
                    elem.pitch.midi = normalized_pitch
                    print(f"Note {original_pitch} normalized to {elem.pitch} in octave {target_octave}.")

    # Save the normalized MIDI file
    midi_data.write('midi', fp=output_file)
    print(f"Normalized MIDI saved to {output_file}.")
    
    
    
def fix_far_notes(notes, validation_report, chord_map, measure_number):
    """
    Fix notes in a measure that have a distance of at least 7 semitones from one neighbor
    and at least 4 semitones from the other. Adjust the note to a valid note within the range
    defined by its neighbors, including edge notes, and account for octave normalization.
    Parameters:
    - notes: List of tuples (MIDI number, start time) for the measure.
    - validation_report: Dictionary mapping measure numbers to note details.
    - chord_map: Dictionary mapping chords to valid notes.
    - measure_number: Measure number (for logging/debugging).
    Returns:
    - Updated list of notes with adjustments.
    """
    from music21 import note
    import logging
    logging.info(f"Processing measure {measure_number} to fix far notes.")
    print(f"Processing measure {measure_number}...")
    updated_notes = notes[:]
    # Iterate over all notes in the measure
    for i, (current_note_midi, start_time) in enumerate(notes):
        # Determine the chord for the current note
        current_chord = None
        for val_note_name, _, chord in validation_report[measure_number]:
            if note.Note(current_note_midi).name == val_note_name:
                current_chord = chord.replace("Expected in ", "").replace("Valid in ", "").strip()
                break
        if not current_chord:
            logging.error(f"[Measure {measure_number}] No chord found for note {current_note_midi}. Skipping adjustment.")
            print(f"⚠️  [Measure {measure_number}] No chord found for note {current_note_midi}. Skipping adjustment.")
            continue
        if current_chord not in chord_map:
            logging.error(f"[Measure {measure_number}] Chord {current_chord} not found in chord_map!")
            print(f"❌  [Measure {measure_number}] Chord {current_chord} not found in chord_map!")
            continue
        # Determine valid notes from the chord
        valid_chord_notes = sorted([note.Note(n).pitch.midi for n in chord_map[current_chord]])
        print(f"[Measure {measure_number}] Valid chord notes: {valid_chord_notes}")
        # Identify the neighbors
        if i == 0:  # First note (edge case)
            left_neighbor = None
            right_neighbor = notes[i + 1][0]
            range_start = right_neighbor - 7  # Start range based on the right neighbor
            range_end = right_neighbor + 7
            print(f"🔹 [Edge Note] First note. Neighbor = {right_neighbor}, Range: {range_start}-{range_end}.")
        elif i == len(notes) - 1:  # Last note (edge case)
            left_neighbor = notes[i - 1][0]
            right_neighbor = None
            range_start = left_neighbor - 7  # Start range based on the left neighbor
            range_end = left_neighbor + 7
            print(f"🔹 [Edge Note] Last note. Neighbor = {left_neighbor}, Range: {range_start}-{range_end}.")
        else:  # Non-edge notes
            left_neighbor = notes[i - 1][0]
            right_neighbor = notes[i + 1][0]
            range_start = min(left_neighbor, right_neighbor)
            range_end = max(left_neighbor, right_neighbor)
        # Expand the range incrementally and find potential notes
        def get_octave_normalized_notes(notes, start, end):
            potential = []
            for n in notes:
                if start <= n <= end:
                    potential.append(n)
                if start <= n - 12 <= end:  # Down one octave
                    potential.append(n - 12)
                if start <= n + 12 <= end:  # Up one octave
                    potential.append(n + 12)
            return sorted(set(potential))
        potential_notes = []
        for expansion in range(4):  # Expand up to ±3 semitones
            expanded_range_start = range_start - expansion
            expanded_range_end = range_end + expansion
            potential_notes = get_octave_normalized_notes(valid_chord_notes, expanded_range_start, expanded_range_end)
            print(f"  🔍 Expanded range {expanded_range_start}-{expanded_range_end}. Potential notes: {potential_notes}")
            if potential_notes:
                break
        # Replace the current note with the closest valid note
        if potential_notes:
            best_note = min(potential_notes, key=lambda n: abs(n - current_note_midi))
            print(f"  🎯 Found valid note {best_note}. Replacing {current_note_midi}.")
        else:
            best_note = current_note_midi  # Default to itself if no valid note is found
            print(f"  ⚠️  No valid notes found in expanded ranges. Keeping {current_note_midi}.")
        logging.info(
            f"[Measure {measure_number}] Replacing note {current_note_midi} with {best_note}."
        )
        updated_notes[i] = (best_note, start_time)
    print(f"✅ Finished processing measure {measure_number}.\n")
    return updated_notes




def correct_midi(midi_file, validation_report, chord_map, output_file):
    """
    Correct a MIDI file based on the validation report by shifting notes to the nearest valid pitch.

    Parameters:
    - midi_file: Path to the input MIDI file.
    - validation_report: The validation report with invalid notes and their expected chords.
    - chord_map: Dictionary mapping chords to their valid notes.
    - output_file: Path to save the corrected MIDI file.
    """
    from music21 import converter, note
    import logging
    

    # Enable logging
    logging.basicConfig(level=logging.DEBUG)
    print("*****************************************************")

    # Parse the MIDI file
    midi_data = converter.parse(midi_file)
    
    def calculate_relative_distances(notes):
        """Calculate the relative distances between notes."""
        distances = {}
        for (note1, start1), (note2, start2) in itertools.combinations(notes, 2):
            distance = abs(note1 - note2)
            distances[(start1, start2)] = distance
        return distances
    
    initial_distances = {}

    # Iterate over each measure and correct invalid notes
    for part in midi_data.parts:
        for measure in part.getElementsByClass('Measure'):
            measure_number = measure.number

            # Gather all notes in the measure before corrections
            notes_in_measure = [
                (elem.pitch.midi, round(elem.offset / measure.quarterLength, 4))
                for elem in measure.notes
            ]
            initial_distances[measure_number] = calculate_relative_distances(notes_in_measure)

    # Iterate over each measure and correct invalid notes
    for part in midi_data.parts:
        for measure in part.getElementsByClass('Measure'):
            measure_number = measure.number

            if measure_number in validation_report:
                for note_name, start_time, expected_chord in validation_report[measure_number]:
                    # Skip valid notes
                    if expected_chord.startswith("Valid in"):
                        continue

                    # Extract the chord name by removing "Expected in " prefix
                    chord_name = expected_chord.replace("Expected in ", "").strip()

                    # Get the valid notes for the expected chord
                    if chord_name not in chord_map:
                        raise KeyError(f"Chord {chord_name} not found in chord_map!")

                    valid_notes = chord_map[chord_name]

                    for elem in measure.notes:
                        # if isinstance(elem, note.Note):
                            elem_start_time = round(elem.offset / measure.quarterLength, 4)
                            if elem.name == note_name and elem_start_time == start_time:
                                # Log current note and valid notes
                                current_midi = elem.pitch.midi
                                # logging.debug(
                                #     f"DEBUG: Measure {measure_number}: Current note {note_name} "
                                #     f"(MIDI: {current_midi}), Start time: {elem_start_time}, "
                                #     f"Valid notes: {valid_notes}"
                                # )
                                print(
                                    f"DEBUG: Measure {measure_number}: Current note {note_name} "
                                    f"(MIDI: {current_midi}), Start time: {elem_start_time}, "
                                    f"Valid notes: {valid_notes}"
                                )

                                # Calculate cyclic distances to all valid notes
                                distances = {
                                    valid_note: cyclic_distance(current_midi, note.Note(valid_note).pitch.midi)
                                    for valid_note in valid_notes
                                }

                                # Log distances for debugging
                                # logging.debug(
                                #     f"DEBUG: Measure {measure_number}: Distances to valid notes: {distances}"
                                # )
                                print(
                                    f"DEBUG: Measure {measure_number}: Distances to valid notes: {distances}"
                                )

                                # Find the closest valid note
                                shifted_pitch = min(
                                    distances,
                                    key=distances.get,
                                )

                                # Log the correction
                                # logging.debug(
                                #     f"DEBUG: Measure {measure_number}: Shifting note {note_name} "
                                #     f"to {shifted_pitch} for {chord_name}"
                                # )
                                print(
                                    f"DEBUG: Measure {measure_number}: Shifting note {note_name} "
                                    f"to {shifted_pitch} for {chord_name}"
                                )

                                # Correct the note
                                elem.name = shifted_pitch

            # Apply gap-based corrections
            # updated_notes = find_and_replace_large_gaps(notes_in_measure, validation_report, chord_map, measure_number)

            # # Replace notes in the MIDI data based on updated notes
            # for elem, (new_note, _) in zip(measure.notes, updated_notes):
            #     elem.name = note.Note(new_note).name
                
    # Save the corrected MIDI file
    midi_data.write('midi', fp=output_file)
    # logging.info(f"Corrected MIDI saved to {output_file}")
    
    corrected_distances = {}
    midi_data_corrected = converter.parse(output_file)
    for part in midi_data_corrected.parts:
        for measure in part.getElementsByClass('Measure'):
            measure_number = measure.number
            notes_in_measure = [
                (elem.pitch.midi, round(elem.offset / measure.quarterLength, 4))
                for elem in measure.notes
            ]
            updated_notes = find_and_replace_large_gaps(notes_in_measure, validation_report, chord_map, measure_number)
            
            updated_notes = fix_far_notes(notes_in_measure, validation_report, chord_map, measure_number)
            
            updated_notes = correct_hanging_notes(updated_notes)
                        
            for elem, (new_note, _) in zip(measure.notes, updated_notes):
                # if isinstance(elem, note.Note):
                    elem.name = note.Note(new_note).name
                    
            corrected_distances[measure_number] = calculate_relative_distances(notes_in_measure)

    # Log the comparisons
    for measure_number in initial_distances:
        # logging.info(f"Measure {measure_number}: Initial distances -> {initial_distances[measure_number]}")
        # logging.info(f"Measure {measure_number}: Corrected distances -> {corrected_distances[measure_number]}")
        print(f"Measure {measure_number}: Initial distances -> {initial_distances[measure_number]}")
        print(f"Measure {measure_number}: Corrected distances -> {corrected_distances[measure_number]}")




def distance_based_octave_normalization(midi_file, output_file):
    """
    Perform distance-based octave normalization on a MIDI file.
    Adjust the octave of each note to minimize its collective distance
    from its immediate neighbors while preserving note durations.
    
    Parameters:
    - midi_file: Path to the input MIDI file.
    - output_file: Path to save the normalized MIDI file.
    """
    from music21 import converter, note

    print(f"Performing distance-based octave normalization on {midi_file}.")

    # Parse the MIDI file
    midi_data = converter.parse(midi_file)

    # Collect all notes in sequence (flattening all parts and measures)
    all_notes = []
    for part in midi_data.parts:
        for measure in part.getElementsByClass('Measure'):
            for elem in measure.notes:
                if isinstance(elem, note.Note):
                    all_notes.append(elem)

    # Function to calculate the cumulative distance for a note
    def calculate_distance(index, midi_number):
        left_distance = abs(midi_number - all_notes[index - 1].pitch.midi) if index > 0 else 0
        right_distance = abs(midi_number - all_notes[index + 1].pitch.midi) if index < len(all_notes) - 1 else 0
        return left_distance + right_distance

    # Iterate over each note and adjust its octave
    for i, current_note in enumerate(all_notes):
        original_midi = current_note.pitch.midi

        # Calculate distances for original, octave up, and octave down
        original_distance = calculate_distance(i, original_midi)
        octave_up_distance = calculate_distance(i, original_midi + 12)
        octave_down_distance = calculate_distance(i, original_midi - 12)

        # Select the option that minimizes distance, but only change if it reduces distance
        min_distance = min(original_distance, octave_up_distance, octave_down_distance)

        if min_distance < original_distance:
            if min_distance == octave_up_distance:
                current_note.pitch.midi = original_midi + 12
                print(f"Note {original_midi} shifted up to {current_note.pitch.midi}.")
            elif min_distance == octave_down_distance:
                current_note.pitch.midi = original_midi - 12
                print(f"Note {original_midi} shifted down to {current_note.pitch.midi}.")
        else:
            print(f"Note {original_midi} remains unchanged.")

    # Save the normalized MIDI file
    midi_data.write('midi', fp=output_file)
    print(f"Final normalized MIDI saved to {output_file}.")
    
    
# # Example usage
# chord_map = {
#     # Major chords
#     "Cmajor": ['C', 'E', 'G'],
#     "C#major": ['C#', 'F', 'G#'],
#     "Dmajor": ['D', 'F#', 'A'],
#     "D#major": ['D#', 'G', 'A#'],
#     "Emajor": ['E', 'G#', 'B'],
#     "Fmajor": ['F', 'A', 'C'],
#     "F#major": ['F#', 'A#', 'C#'],
#     "Gmajor": ['G', 'B', 'D'],
#     "G#major": ['G#', 'C', 'D#'],
#     "Amajor": ['A', 'C#', 'E'],
#     "A#major": ['A#', 'D', 'F'],
#     "Bmajor": ['B', 'D#', 'F#'],

#     # Minor chords
#     "Cminor": ['C', 'D#', 'G'],
#     "C#minor": ['C#', 'E', 'G#'],
#     "Dminor": ['D', 'F', 'A'],
#     "D#minor": ['D#', 'F#', 'A#'],
#     "Eminor": ['E', 'G', 'B'],
#     "Fminor": ['F', 'G#', 'C'],
#     "F#minor": ['F#', 'A', 'C#'],
#     "Gminor": ['G', 'A#', 'D'],
#     "G#minor": ['G#', 'B', 'D#'],
#     "Aminor": ['A', 'C', 'E'],
#     "A#minor": ['A#', 'C#', 'F'],
#     "Bminor": ['B', 'D', 'F#'],
# }

    
    
def note_to_midi(root, chord_type="major"):
    """
    Convert a chord root and type to a list of MIDI notes.
    """
    from music21 import chord, pitch

    # Remove any octave information from the root (e.g., 'A#2' -> 'A#')
    root = ''.join([char for char in root if not char.isdigit()])

    # Clean up the chord type to remove "triad" if present and ensure correct formatting
    chord_type = chord_type.replace("triad", "").strip()

    try:
        # Construct the chord using a space separator between root and chord type
        constructed_chord = chord.Chord(f"{root} {chord_type}")
        midi_notes = [note.midi for note in constructed_chord.pitches]
    except Exception as e:
        raise ValueError(f"Error converting chord {root} {chord_type} to MIDI: {e}")

    return midi_notes



    
def transpose_to_key(midi_data, target_key):
    """
    Transpose the MIDI data to the target key.
    """
    current_key = midi_data.analyze('key')
    print(f"Original Key: {current_key}")
    interval_to_target = interval.Interval(current_key.tonic, target_key.tonic)
    transposed_data = midi_data.transpose(interval_to_target)
    print(f"Transposed to: {target_key}")
    return transposed_data

def analyze_bass_chords_by_bars(is_backing_track, midi_data, consolidate_bars=1, convert_flats=True, deduplicate=True):
    """
    Analyze a MIDI file to extract bass chord progression, focusing on the lowest notes,
    and group the chords bar-wise or by specified bar groups.

    Deduplicates consecutive identical chords within bars and prioritizes chords with longer durations.
    """
    from collections import defaultdict

    # Chordify the music data
    chords = midi_data.chordify()

    # Prepare a dictionary for bar-wise analysis
    bar_wise_chords = defaultdict(list)

    for measure in chords.getElementsByClass(stream.Measure):
        bar_number = measure.number
        last_chord = None  # For deduplication check within a bar
        for elem in measure.notesAndRests:
            if isinstance(elem, chord.Chord):
                bass_note = elem.bass()
                chord_name = elem.commonName

                # Convert flat notes (`B-`) to enharmonic equivalent if specified
                if convert_flats and "-" in bass_note.name:
                    bass_note = bass_note.getEnharmonic()

                chord_repr = (bass_note.nameWithOctave, chord_name, elem.quarterLength)

                # Deduplicate consecutive chords, prioritize longer durations
                if deduplicate:
                    if last_chord and last_chord[:2] == chord_repr[:2]:
                        # Replace only if the current chord has longer duration
                        if chord_repr[2] > last_chord[2]:
                            bar_wise_chords[bar_number][-1] = chord_repr
                        continue

                bar_wise_chords[bar_number].append(chord_repr)
                last_chord = chord_repr

    # Simplify chords into grouped bars
    grouped_chords = defaultdict(list)
    for bar in sorted(bar_wise_chords.keys()):
        group = (bar - 1) // consolidate_bars + 1
        grouped_chords[group].extend(bar_wise_chords[bar])
        
    # Check for "leaked" notes in the final bar (vocal melody case)
    if grouped_chords:
        last_group = max(grouped_chords.keys())
        if last_group > 1:  # Ensure there is at least one previous bar
            final_bar_chords = grouped_chords[last_group]
            previous_bar_chords = grouped_chords[last_group - 1]

            # If the final bar has only one note and it matches the last note of the previous bar
            if len(final_bar_chords) == 1:
                final_bass_note = final_bar_chords[0][0]  # Extract bass note of the final chord
                previous_last_bass_note = previous_bar_chords[-1][0]  # Extract bass note of the last chord in previous bar

                if final_bass_note == previous_last_bass_note:
                    # Drop the final bar's chord(s)
                    print(f"Removing leaked note {final_bass_note} from final bar {last_group}")
                    del grouped_chords[last_group]

    # Format grouped chords
    simplified_bars = {
        group: [f"{bass}-{name}" for bass, name, _ in grouped_chords[group]]
        for group in grouped_chords
    }
    
    if is_backing_track:
        # Add filtering to remove '-note' entries
        simplified_bars = {
            bar: [chord for chord in chords if not chord.endswith("-note")]
            for bar, chords in simplified_bars.items()
        }

    print("\nBar-Wise Chord Progression:")
    for group, chords in simplified_bars.items():
        start_bar = consolidate_bars * (group - 1) + 1
        end_bar = consolidate_bars * group
        print(f"Bars {start_bar}-{end_bar}: {', '.join(chords)}")

    return simplified_bars


def analyze_midi(midi_file, bpm=120, is_backing_track = False, target_key=None, convert_flats=True, consolidate_bars=1, 
                 velocity_threshold=10, duration_threshold=0.1):
    """
    Analyze a MIDI file to detect key, transpose if necessary, extract chord progression, pseudo-chords, 
    melodic intervals, and the first significant note start time.
    """
    # Parse MIDI file
    print("analyze_midi working for ", midi_file)
    music_data = converter.parse(midi_file)

    # Transpose to target key if provided
    if target_key:
        music_data = transpose_to_key(music_data, target_key)

    # Analyze the key
    key_signature = music_data.analyze('key')
    print(f"Detected Key: {key_signature}")
    print("************* BEWARE : Flat note conversion to Sharp denotion is turned off here *************")
    # if "-" in key_signature.tonic.name:
    #     enharmonic_key = key_signature.tonic.getEnharmonic()
    #     print(f"Key Signature converted from {key_signature} to {enharmonic_key}")
    #     key_signature = enharmonic_key

    # Extract bar-wise bass chords
    bar_wise_chords = analyze_bass_chords_by_bars(is_backing_track, music_data, consolidate_bars=consolidate_bars)
    
    # Detect Tempo
    tempo = bpm  # Default tempo
    for el in music_data.flatten().getElementsByClass(tempo):
        tempo = el.number
        break  # Take the first detected tempo
    
    print(f"Detected Tempo: {tempo} BPM")

    # Find the first significant note (timing detection)
    first_significant_note = None
    first_significant_time = None
    second_significant_note = None
    second_significant_time = None 
    for part in music_data.parts:  # Iterate over parts
        for elem in part.flatten().notes:  # Flatten to get all notes
            if elem.volume.velocity >= velocity_threshold and (elem.quarterLength >= duration_threshold):
                first_significant_note = elem
                first_significant_time = elem.offset  # Time in quarter lengths
                break
        if first_significant_note:
            real_time = first_significant_time * (60 / tempo)
            print(f"First significant note: {first_significant_note} starts at time {real_time:.2f} seconds")
            break  # Exit loop once first significant note is found
        else:
            real_time = None

    if first_significant_note:
        print(f"First significant note: {first_significant_note} starts at time {first_significant_time}")

    # Group simultaneous notes into pseudo-chords and handle them bar-wise
    bar_wise_pseudo_chords = {}
    for measure in music_data.chordify().getElementsByClass(stream.Measure):
        bar_number = measure.number
        pseudo_chords = []

        for elem in measure.notesAndRests:
            if isinstance(elem, chord.Chord):
                # Collect pitch names for chords
                pitch_names = []
                for pitch in elem.pitches:
                    # Convert flats (`B-`) to enharmonic equivalents if specified
                    if convert_flats and "-" in pitch.name:
                        pitch_names.append(pitch.getEnharmonic().name)
                    else:
                        pitch_names.append(pitch.name)

                chord_quality = elem.quality
                pseudo_chords.append((pitch_names, chord_quality))

        if pseudo_chords:
            bar_wise_pseudo_chords[bar_number] = pseudo_chords

    # Combine pseudo-chords based on consolidate_bars
    combined_pseudo_chords = defaultdict(list)
    for bar in sorted(bar_wise_pseudo_chords.keys()):
        group = (bar - 1) // consolidate_bars + 1
        combined_pseudo_chords[group].extend(bar_wise_pseudo_chords[bar])
        
    if is_backing_track:
        # Filter out invalid pseudo-chords with only one note and scale 'other'
        for group in combined_pseudo_chords:
            combined_pseudo_chords[group] = [
                pseudo_chord for pseudo_chord in combined_pseudo_chords[group]
                if not (len(pseudo_chord[0]) == 1 and pseudo_chord[1] == 'other')
            ]

    # Convert combined pseudo-chords into arrays
    combined_pseudo_chords_array = [
        combined_pseudo_chords[group] for group in sorted(combined_pseudo_chords.keys())
    ]

    print("Filtered Pseudo-Chords (Bar-Wise):")
    for group, pseudo_chords in combined_pseudo_chords.items():
        start_bar = consolidate_bars * (group - 1) + 1
        end_bar = consolidate_bars * group
        print(f"Bars {start_bar}-{end_bar}: {pseudo_chords}")

    # Analyze intervals between successive notes for melodic insights
    notes_and_chords = [elem for elem in music_data.flatten().notesAndRests]
    note_objects = []

    for elem in notes_and_chords:
        if isinstance(elem, note.Note):
            note_objects.append(elem)
        elif isinstance(elem, chord.Chord):
            note_objects.append(elem.root())

    melodic_intervals = [
        interval.Interval(note_objects[i], note_objects[i + 1]).name
        for i in range(len(note_objects) - 1)
    ]

    print("Melodic Intervals:")
    print(melodic_intervals)

    return {
        "key": key_signature,
        "bar_wise_chords": bar_wise_chords,
        "pseudo_chords": combined_pseudo_chords_array,
        "combined_pseudo_chords": combined_pseudo_chords,
        "melodic_intervals": melodic_intervals,
        "first_vocal_start": {
            "note": first_significant_note if first_significant_note else None,
            "time": first_significant_time if first_significant_time else None,
            "real_time_seconds": real_time
        }
    }




def add_gaps_to_midi(midi_path, output_path, gap_positions, bpm=120, gap_duration_in_beats=4):
    """
    Add gaps of specified duration to a MIDI file after specific notes.

    :param midi_path: Path to the input MIDI file.
    :param output_path: Path to save the output MIDI file.
    :param gap_positions: Array of numbers specifying after which notes to add gaps.
    :param bpm: Tempo of the MIDI file in beats per minute.
    :param gap_duration_in_beats: Duration of the gap in beats (default: 4 beats = 1 whole note).
    """
    # Load the MIDI file
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    
    # Calculate the gap duration in seconds based on BPM
    seconds_per_beat = 60 / bpm
    gap_duration_in_seconds = (gap_duration_in_beats * seconds_per_beat)/2

    # Iterate through each instrument in the MIDI file
    for instrument in midi_data.instruments:
        # Sort notes by start time (in case they are not ordered)
        instrument.notes.sort(key=lambda note: note.start)

        # Insert gaps by modifying the start and end times of subsequent notes
        adjusted_notes = []
        note_counter = 0  # Tracks the index of the current note
        last_end_time = 0  # Tracks the end time of the last processed note

        for note in instrument.notes:
            # Increment the note counter
            note_counter += 1

            # Adjust the start and end times of the current note
            note_start = max(note.start, last_end_time)
            note_end = note_start + (note.end - note.start)
            adjusted_notes.append(pretty_midi.Note(velocity=note.velocity, pitch=note.pitch, start=note_start, end=note_end))

            # If the note index matches a gap position, add the gap
            if note_counter in gap_positions:
                last_end_time = note_end + gap_duration_in_seconds
            else:
                last_end_time = note_end

        # Replace the notes with the adjusted notes
        instrument.notes = adjusted_notes

    # Write the modified MIDI data to the output file
    midi_data.write(output_path)
    print(f"Modified MIDI file saved to: {output_path}")
    
    
def map_to_scale_degree(note, key, scale):
    """Map MIDI notes to scale degrees."""
    key_offset = pretty_midi.note_name_to_number(key)
    scale_notes = Key(key, scale).scale.semitones
    return (note - key_offset) % 12 if (note - key_offset) % 12 in scale_notes else None



def chord_to_notes(chord_name: str, key_name="C", scale_name="major", min_note=45, max_note=72):
    """
    Generate all notes for a given chord, ensuring they adhere to the key, scale, and note range.
    """
    key = Key(key_name, scale_name)
    root_midi_note = note_name_to_midi_note(chord_name)
    scale_notes = key.scale.semitones
    
    chord_intervals = {
        "major": [0, 4, 7],  # Root, Major 3rd, Perfect 5th
        "minor": [0, 3, 7],  # Root, Minor 3rd, Perfect 5th
        # Add more chord types as needed
    }
    chord_type = "major"  # Default to major, update as needed
    
    notes = []
    for interval in chord_intervals[chord_type]:
        note = root_midi_note + interval
        if note % 12 in scale_notes:  # Ensure note is in the scale
            while note < min_note:
                note += 12
            while note > max_note:
                note -= 12
            notes.append(note)
    
    return notes


def get_chord_progression_for_section(section_length, progression):
    """
    Distribute chords across the section length. 
    Example: Progression = ["A#", "C", "F"]
    """
    chords = []
    bars_per_chord = max(1, section_length // len(progression))
    for chord in progression:
        chords.extend([chord] * bars_per_chord)
    return chords[:section_length]


def add_gaps_to_durations(durations, gap_positions, gap_duration=4.0):
    """Add gaps after specified numbers of notes."""
    modified_durations = []
    note_count = 0

    for duration in durations:
        modified_durations.append(duration)
        note_count += 1
        if gap_positions and note_count == gap_positions[0]:
            modified_durations.append(gap_duration)  # Add gap duration
            gap_positions.pop(0)  # Remove the applied gap position

    return modified_durations

def combine_sections(
    output_folder="outputs/sections",
    final_output_path="outputs/generated_sequence_final.mid",
    bpm=120,
    initial_gap_beats=2,
    section_gap_beats=2,
    ending_gap_beats=2
):
    """
    Combine all section MIDI files sequentially into one using pretty_midi.
    Ensures configurable gaps at the beginning, between sections, and at the end.
    """
    import pretty_midi
    import os
    import re

    # Normalize the paths
    output_folder = os.path.normpath(output_folder)
    final_output_path = os.path.normpath(final_output_path)
    
    def round_to_quarter(value):
        """Round the value to the nearest quarter (0.25, 0.50, 0.75, X.00)."""
        return round(value * 4) / 4

    # Look for files matching the pattern corrected_section_bar<range>.mid
    pattern = re.compile(r"corrected_section_bar\d+-\d+\.mid")
    section_files = sorted(
        [f for f in os.listdir(output_folder) if pattern.match(f)],
        key=lambda x: int(re.search(r'(\d+)-', x).group(1))  # Sort by the first number in the range
    )

    # Create a PrettyMIDI object for the combined MIDI
    combined_midi = pretty_midi.PrettyMIDI()

    # Initialize an empty track
    combined_instrument = pretty_midi.Instrument(program=0)  # Default program 0: Acoustic Grand Piano

    # Calculate the durations of the gaps in seconds
    initial_gap_duration = (60 / bpm) * initial_gap_beats
    section_gap_duration = (60 / bpm) * section_gap_beats
    ending_gap_duration = (60 / bpm) * ending_gap_beats
    beat_duration = 60 / bpm  # Duration of one beat in seconds
    bar_duration = beat_duration * 4  # Duration of one bar in seconds (assuming 4/4 time signature)

    # Track the cumulative time in seconds
    cumulative_time = initial_gap_duration

    # # Track the cumulative time in seconds
    # cumulative_time = 0.0

    # # Add silence at the beginning
    # silent_note_start = pretty_midi.Note(
    #     velocity=0, pitch=0, start=cumulative_time, end=cumulative_time + initial_gap_duration
    # )
    # combined_instrument.notes.append(silent_note_start)
    # cumulative_time += initial_gap_duration
    print(f"Added {initial_gap_beats} beats of silence at the start, duration: {initial_gap_duration:.2f}s")

    for section_index, section_file in enumerate(section_files):
        section_path = os.path.join(output_folder, section_file)
        print(f"Processing Section {section_index + 1} from path: {os.path.abspath(section_path)}")

        # Load the section MIDI using pretty_midi
        section_midi = pretty_midi.PrettyMIDI(section_path)

        # # Track the last note's end time for alignment
        # section_end_time = 0.0
        
         # Determine the desired rounded bar start time
        section_start_bar = cumulative_time / bar_duration
        rounded_start_bar = round_to_quarter(section_start_bar)
        adjusted_start_time = rounded_start_bar * bar_duration
        # Ensure the section starts at the rounded bar time
        alignment_offset = adjusted_start_time - cumulative_time
        print(f"Section {section_index + 1} starts at bar: {section_start_bar:.2f}, rounded to: {rounded_start_bar:.2f}")
        print(f"Alignment offset: {alignment_offset:.2f}s")

        # Track the last note's end time for alignment
        section_end_time = adjusted_start_time

        for instrument in section_midi.instruments:
            for note in instrument.notes:
                # Adjust the start and end times of each note by the cumulative time
                # note.start += cumulative_time
                # note.end += cumulative_time
                
                 # Adjust the start and end times of each note by the alignment offset
                note.start += adjusted_start_time
                note.end += adjusted_start_time
                combined_instrument.notes.append(note)

                # Track the latest end time of notes in the section
                section_end_time = max(section_end_time, note.end)

        # Log details of the section
        # print(f"Section {section_index + 1} duration: {section_end_time - cumulative_time:.2f}s, "
        #       f"start time: {cumulative_time:.2f}s, end time: {section_end_time:.2f}s")
        
        print(f"Section {section_index + 1} duration after alignment: {section_end_time - adjusted_start_time:.2f}s, "
              f"start time: {adjusted_start_time:.2f}s, end time: {section_end_time:.2f}s")

        # Update the cumulative time to the end of the section
        cumulative_time = section_end_time

        # Add a silent gap after the section (if not the last section)
        if section_index < len(section_files) - 1:
            silent_note = pretty_midi.Note(
                velocity=0, pitch=0, start=cumulative_time, end=cumulative_time + section_gap_duration
            )
            combined_instrument.notes.append(silent_note)
            cumulative_time += section_gap_duration
            print(f"Added silent gap of {section_gap_duration:.2f}s after Section {section_index + 1}, "
                #   f"gap start: {section_end_time:.2f}s, gap end: {cumulative_time:.2f}s")
                f"gap start: {cumulative_time - section_gap_duration:.2f}s, gap end: {cumulative_time:.2f}s")

    # Add silence at the end of the final section
    silent_note_end = pretty_midi.Note(
        velocity=0, pitch=0, start=cumulative_time, end=cumulative_time + ending_gap_duration
    )
    combined_instrument.notes.append(silent_note_end)
    cumulative_time += ending_gap_duration
    print(f"Added {ending_gap_beats} beats of silence at the end, duration: {ending_gap_duration:.2f}s, "
          f"end time: {cumulative_time:.2f}s")

    # Add the combined instrument to the PrettyMIDI object
    combined_midi.instruments.append(combined_instrument)

    # Save the combined MIDI file
    combined_midi.write(final_output_path)
    print(f"Final combined MIDI saved to {os.path.abspath(final_output_path)}")


def adjust_large_intervals_in_midi(input_midi_path, output_midi_path, detected_key):
    """
    Adjusts notes in a MIDI file if the interval between consecutive notes exceeds 8 semitones.
    Notes are adjusted to the detected key's root note.
    """
    try:
        # Convert the detected_key to a MIDI note number
        root_note = pretty_midi.note_name_to_number(detected_key)

        midi = PrettyMIDI(input_midi_path)
        
        for instrument in midi.instruments:
            adjusted_notes = []
            prev_note = None

            for note in instrument.notes:
                if prev_note is not None and abs(note.pitch - prev_note.pitch) > 8:
                    logging.info(f"Adjusting note {note.pitch} to {root_note} due to large interval from {prev_note.pitch}")
                    adjusted_note = pretty_midi.Note(
                        velocity=note.velocity,
                        pitch=root_note,  # Adjust pitch to root note
                        start=note.start,
                        end=note.end
                    )
                    adjusted_notes.append(adjusted_note)
                else:
                    adjusted_notes.append(note)
                prev_note = note  # Update the previous note

            # Replace the instrument's notes with the adjusted ones
            instrument.notes = adjusted_notes

        # Save the updated MIDI file
        midi.write(output_midi_path)
        logging.info(f"Adjusted MIDI file saved to: {output_midi_path}")

    except Exception as e:
        logging.error(f"Failed to adjust large intervals in MIDI file: {e}")


def adjust_to_octave_range(chord_notes, reference_sequence):
    """
    Adjust the chord notes to be in the same octave range as the reference sequence.
    
    Args:
        chord_notes (list): List of MIDI numbers for the chord notes.
        reference_sequence (list): List of MIDI numbers in the reference sequence.
    
    Returns:
        list: Chord notes adjusted to the same octave range.
    """
    adjusted_notes = []
    min_ref = min(reference_sequence)
    max_ref = max(reference_sequence)
    
    for note in chord_notes:
        # Adjust the note until it fits in the range of reference_sequence
        while note < min_ref:
            note += 12  # Move up an octave
        while note > max_ref:
            note -= 12  # Move down an octave
        adjusted_notes.append(note)
    
    return adjusted_notes


def pitch_class_to_midi(pitch_class):
    """
    Convert a pitch class (e.g., 'C#') to its MIDI pitch number in all octaves (ignores octave).
    """
    # Map of pitch classes to their MIDI pitch numbers in a single octave
    pitch_to_midi = {
        'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
        'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
    }
    # Get the MIDI pitch number for the given pitch class
    if pitch_class not in pitch_to_midi:
        raise ValueError(f"Invalid pitch class: {pitch_class}")
    return pitch_to_midi[pitch_class]

def generate_bar_pair_info(filtered_progressions, line_level_total_syllables):
    """
    Generate a JSON structure with information about each bar pair, ensuring that note counts
    are correctly mapped to bar pairs based on their positional order.

    Parameters:
    - filtered_progressions: A dictionary mapping chord progressions to bar pairs.
    - line_level_total_syllables: A list containing the number of notes (syllables) for each line.

    Returns:
    - A JSON-like dictionary mapping each bar pair to its progression and note count.
    """
    bar_pair_info = {}
    # Flatten all bar pairs from filtered_progressions
    all_bar_pairs = []
    for progression, bar_pairs in filtered_progressions.items():
        all_bar_pairs.extend(bar_pairs)

    # Parse the bar pairs to determine their positional indices
    bar_positions = {}
    for bar_pair in all_bar_pairs:
        # Extract the bar number (e.g., 'bar5-6' -> 5)
        first_bar = int(bar_pair.split('-')[0].replace('bar', ''))
        bar_positions[bar_pair] = first_bar

    # Sort bar pairs by their positional order
    sorted_bar_pairs = sorted(bar_positions.items(), key=lambda x: x[1])

    # Assign note counts based on positional order
    for idx, (bar_pair, _) in enumerate(sorted_bar_pairs):
        if idx >= len(line_level_total_syllables):
            raise ValueError("The number of bar pairs exceeds the number of note counts provided!")

        # Assign note count from the correct position
        note_count = line_level_total_syllables[idx]
        # Find the progression associated with the bar pair
        progression = None
        for prog, bars in filtered_progressions.items():
            if bar_pair in bars:
                progression = prog
                break

        if progression is None:
            raise ValueError(f"No chord progression found for bar pair: {bar_pair}")

        bar_pair_info[bar_pair] = {
            "chord_progression": progression,
            "note_count": note_count,
            "melody_generated": False,
        }

    return bar_pair_info



def analyze_note_start_times(midi_file):
    """
    Analyze the start time of each note in a MIDI file and express it as a fraction or decimal
    of a whole bar.

    Parameters:
    - midi_file: Path to the input MIDI file.

    Returns:
    - A dictionary with measures as keys and a list of tuples as values,
      where each tuple contains the note and its start time as a fraction of the bar.
    """
    # Parse the MIDI file
    midi_data = converter.parse(midi_file)
    
    # Store results
    note_start_times = {}

    # Analyze each part and measure
    for part in midi_data.parts:
        for measure in part.getElementsByClass('Measure'):
            measure_number = measure.number
            measure_length = measure.quarterLength  # Total length of the measure in quarter notes
            notes_in_measure = []

            for elem in measure.notes:
                # if isinstance(elem, note.Note):
                    print(f"type of {elem} is : ", type(elem))
                    start_time_fraction = elem.offset / measure_length
                    notes_in_measure.append((elem.name, round(start_time_fraction, 4)))

            if notes_in_measure:
                note_start_times[measure_number] = notes_in_measure

    return note_start_times

def clean_chord_name(chord_name):
    """Remove octave numbers from chord names."""
    return ''.join(char for char in chord_name if not char.isdigit())


def validate_notes_against_chords(midi_file, bar_pair, bar_pair_info, progression_map):
    """
    Validate the notes in a MIDI file for a given bar pair against its chord progression.

    Parameters:
    - midi_file: Path to the input MIDI file.
    - bar_pair: Name of the bar pair (e.g., 'bar3-4').
    - bar_pair_info: Dictionary with bar pair information, including chord progressions.
    - progression_map: Map detailing how progression spreads across bars.

    Returns:
    - A report detailing all notes and whether they match the chord progression.
    """
    import logging

    # Enable logging
    logging.basicConfig(level=logging.DEBUG)

    # Get the chord progression for the bar pair
    chord_progression = bar_pair_info[bar_pair]['chord_progression']

    # Preprocess progression_map to align chord keys
    def preprocess_progression_map(progression_map):
        processed_map = {}
        for key, value in progression_map.items():
            processed_key = tuple(
                tuple(chord.split('-')[0] + ('major' if 'major' in chord else 'minor') for chord in sub_key)
                for sub_key in key
            )
            processed_map[processed_key] = value
        return processed_map

    processed_map = preprocess_progression_map(progression_map)

    # Find the corresponding progression split in progression_map
    for progression_key, bars in processed_map.items():
        if bar_pair in bars:
            progression_split = progression_key
            break
    else:
        raise ValueError(f"Bar pair {bar_pair} not found in progression_map!")

    # Extract the chord allocation for the two bars
    first_bar_chords, second_bar_chords = progression_split

    # Note-to-chord map for validation
    # chord_map = {
    #     "A#major": set(['A#', 'C', 'F']),
    #     "Cmajor": set(['C', 'E', 'G']),
    #     "Fmajor": set(['F', 'A', 'C']),
    #     "Dminor": set(['D', 'F', 'A']),
    #     "Gminor": set(['G', 'A#', 'D'])
    # }

    # Analyze note start times
    note_start_times = analyze_note_start_times(midi_file)

    # logging.debug(f"Note start times for {bar_pair}: {note_start_times}")

    # Validate notes against chords
    validation_report = {}
    for measure, notes in note_start_times.items():
        validation_report[measure] = []  # Ensure the measure key is always initialized
        measure_fraction = (measure - 1) % 2  # Determine which bar in the pair
        active_chords = first_bar_chords if measure_fraction == 0 else second_bar_chords

        # Divide the bar into fractions based on the number of active chords
        segment_size = 1 / len(active_chords)
        for note_name, start_time in notes:
            # Log note and segment
            segment = min(int(start_time // segment_size), len(active_chords) - 1)
            # logging.debug(
            #     f"Measure {measure}: Note {note_name} starts at {start_time}. "
            #     f"Segment {segment}, Expected Chord: {active_chords[segment]}"
            # )

            # Validate note
            chord_name = clean_chord_name(active_chords[segment])
            valid_notes = chord_map[chord_name]
            if note_name not in valid_notes:
                validation_report[measure].append(
                    (note_name, start_time, f"Expected in {chord_name}")
                )
            else:
                # Include valid notes explicitly in the report
                validation_report[measure].append(
                    (note_name, start_time, f"Valid in {chord_name}")
                )

    return validation_report

def extract_note_sequence(midi_file):
    """
    Extract a sequence of MIDI note numbers from a MIDI file.

    Parameters:
    - midi_file: Path to the input MIDI file.

    Returns:
    - A list of MIDI note numbers representing the sequence of notes in the file.
    """
    # Parse the MIDI file
    midi_data = converter.parse(midi_file)
    
    # Initialize an empty list to store the note sequence
    note_sequence = []

    # Iterate through parts and measures to extract notes
    for part in midi_data.parts:
        for measure in part.getElementsByClass('Measure'):
            for elem in measure.notes:
                # if isinstance(elem, note.Note):
                    # Append the MIDI number of the note
                    note_sequence.append(elem.pitch.midi)

    return note_sequence


def extract_note_details(midi_file):
    """
    Extract sequences of MIDI note numbers, durations, and amplitudes from a MIDI file.

    Parameters:
    - midi_file: Path to the input MIDI file.

    Returns:
    - A dictionary containing:
        - note_sequence: A list of MIDI note numbers.
        - duration_sequence: A list of durations for each note (in quarter lengths).
        - amplitude_sequence: A list of amplitudes (velocities) for each note.
    """
    from music21 import note

    # Parse the MIDI file
    midi_data = converter.parse(midi_file)
    
    # Initialize empty lists to store details
    note_sequence = []
    duration_sequence = []
    amplitude_sequence = []

    # Iterate through parts and measures to extract note details
    for part in midi_data.parts:
        for measure in part.getElementsByClass('Measure'):
            for elem in measure.notes:
                # if isinstance(elem, note.Note):
                    # Append MIDI number of the note
                note_sequence.append(elem.pitch.midi)
                    # Append duration of the note
                duration_sequence.append(elem.quarterLength)
                    # Append amplitude (velocity) of the note, if available
                amplitude_sequence.append(elem.volume.velocity if elem.volume.velocity is not None else 64)  # Default to 64 if velocity is not set

    return {
        "note_sequence": note_sequence,
        "duration_sequence": duration_sequence,
        "amplitude_sequence": amplitude_sequence
    }


def update_bar_pair_info_with_note_sequence(bar_pair_info, first_bar_pair, corrected_output_path):
    """
    Update bar_pair_info with note sequences for bar pairs sharing the same chord progression as first_bar_pair.

    Parameters:
    - bar_pair_info: Dictionary containing bar pair details.
    - first_bar_pair: The bar pair used as a reference for chord progression.
    - corrected_output_path: Path to the corrected MIDI file.

    Returns:
    - Updated bar_pair_info with note_sequence added to applicable bar pairs.
    """
    from copy import deepcopy

    # Extract the chord progression of the first_bar_pair
    reference_chord_progression = bar_pair_info[first_bar_pair]['chord_progression']

    # Extract the note sequence from the corrected MIDI file
    note_sequence = extract_note_sequence(corrected_output_path)
    note_details = extract_note_details(corrected_output_path)
    print(note_details)
    print("note_details[note_sequence]")
    print(note_details["note_sequence"])

    # Add note_sequence to the first_bar_pair
    bar_pair_info[first_bar_pair]['note_sequence'] = note_details["note_sequence"]
    # bar_pair_info[first_bar_pair]['note_sequence'] = note_sequence
    print("normal note_sequence ")
    print(note_sequence)
    bar_pair_info[first_bar_pair]['duration_sequence'] = note_details["duration_sequence"]
    bar_pair_info[first_bar_pair]['amplitude_sequence'] = note_details["amplitude_sequence"]

    # Iterate over all bar pairs in bar_pair_info
    for bar_pair, info in bar_pair_info.items():
        # Check if melody_generated is False and chord_progression matches
        if not info['melody_generated'] and info['chord_progression'] == reference_chord_progression:
            # Add the note_sequence key
            # bar_pair_info[bar_pair]['note_sequence'] = deepcopy(note_sequence)
            bar_pair_info[bar_pair]['note_sequence'] = deepcopy(note_details["note_sequence"])
            bar_pair_info[bar_pair]['duration_sequence'] = deepcopy(note_details["duration_sequence"])
            bar_pair_info[bar_pair]['amplitude_sequence'] = deepcopy(note_details["amplitude_sequence"])

    return bar_pair_info




def generate_melody_with_chord(input_sequence, input_duration_sequence, input_amplitude_sequence, total_notes, chord_notes, filename="generated_melody.mid"):
    """
    Generate a melody based on the given sequence and extend it using a chord for additional notes.
    
    Args:
        input_sequence (list): Base note sequence to follow.
        total_notes (int): Total number of notes desired.
        chord_notes (list): List of MIDI notes representing the chord.
        filename (str): Output MIDI file name.
    """
    # Initialize logging
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

    logging.info(f"Input sequence: {input_sequence}")
    logging.info(f"Chord notes for extension: {chord_notes}")
    logging.info(f"Total desired notes: {total_notes}")

    # Create the initial note sequence
    generated_notes = list(input_sequence)
    generated_duration = list(input_duration_sequence)
    generated_amplitude = list(input_amplitude_sequence)
    
    if len(input_sequence) > total_notes:
        # Trim the sequence if it is longer than the required total_notes
        generated_notes = input_sequence[:total_notes]
        generated_duration = input_duration_sequence[:total_notes]
        generated_amplitude = input_amplitude_sequence[:total_notes]
        logging.info(f"Trimmed sequence: {generated_notes}")
        logging.info(f"Trimmed sequence: {generated_duration}")
        logging.info(f"Trimmed sequence: {generated_amplitude}")

    # Extend the sequence with chord notes if more notes are required
    while len(generated_notes) < total_notes:
        next_note = random.choice(chord_notes)
        generated_notes.append(next_note)
    
    while len(generated_amplitude) < total_notes:
        next_note = 120
        generated_amplitude.append(next_note)
    
    while len(generated_duration) < total_notes:
        next_note = 1.0
        generated_duration.append(next_note)
    
    logging.info(f"Final generated sequence: {generated_notes}")
    
    

    # Create a pattern for the notes
    note_pattern = PSequence(generated_notes, 1)

    # Define a simple amplitude and duration pattern
    amplitude_pattern = PSequence(generated_amplitude, 1)
    duration_pattern = PSequence(generated_duration, 1)
    max_note_duration = 1.0
    if total_notes >= 13:
        print(f"number of notes is {total_notes} so we will reduce max_note_duration to 1/2")
        max_note_duration = 1/2
        min_note_duration = 1 / 2
        duration_pattern = PMap(PSubsequence(dur_markov, 0, number_of_notes), lambda d: clamp(d, min_note_duration, max_note_duration))
    

    # Write to MIDI using Isobar
    output = MidiFileOutputDevice(filename)
    timeline = Timeline(MAX_CLOCK_RATE, output_device=output)
    timeline.stop_when_done = True

    timeline.schedule({
        "note": note_pattern,
        "amplitude": amplitude_pattern,
        "duration": duration_pattern,
        # "gate": 0.9
    })

    # Run the timeline and save to MIDI file
    timeline.run()
    output.write()
    print(f"MIDI file written to: {filename}")
    
    


def markov_generation(bar_pair_name, number_of_notes, reference_vocal_track, reference_octave, backing_analysis, vocal_analysis, consolidated_data, bpm=120, input_note_sequence=None):
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
    
    # midi_analysis_result = analyze_midi(reference_vocal_track)
    midi_analysis_result = vocal_analysis
    print("markov_generation function starts")
    print(f"Detected Key: {midi_analysis_result}")
    
    key_signature = midi_analysis_result["key"]
    print(f"Detected Key: {key_signature}")
    if "-" in key_signature.tonic.name:
        enharmonic_key = key_signature.tonic.getEnharmonic()
        print(f"Key Signature converted from {key_signature} to {enharmonic_key}")
        key_signature = enharmonic_key
        print(key_signature)
    
    detected_key = midi_analysis_result["key"].tonic.name
    if "-" in detected_key:
        detected_key = midi_analysis_result["key"].getEnharmonic()
    detected_scale = midi_analysis_result["key"].mode
    # chord_progression = midi_analysis_result["chords"]
    pseudo_chords = midi_analysis_result["pseudo_chords"]
    melodic_intervals = midi_analysis_result["melodic_intervals"]
        
    # chord_progression_pattern = PSequence(chord_progression, 1)
    pseudo_chord_pattern = PSequence(pseudo_chords, 1)

    print("detected_key ", detected_key)
    print("detected_scale ", detected_scale)
    # print("chord_progression ", chord_progression)
    print("pseudo_chords ", pseudo_chords)
    print("melodic_intervals ", melodic_intervals)
    
    combined_notes, combined_durations, combined_amplitudes, combined_gate, combined_syllables = [], [], [], [], []
    
    # for filename in midi_files:
    # try:
            # logging.info(f"Loading MIDI data from {filename}")
            # midi_input = MidiFileInputDevice(filename)
            # patterns = midi_input.read(quantize=1 / 8)  # Quantize to 1/8th notes
            # print("patterns ", patterns)
                
            # Process lyrics into syllables
            # for item in lyrics:
            #     syllable_counts = calculate_syllable_counts(item["lyrics"])
            #     combined_syllables.extend(syllable_counts)
                
            # combined_syllables = [tuple(syllable) for syllable in combined_syllables]
            # if input_note_sequence == None:
            #     combined_notes.extend(list(patterns[EVENT_NOTE]))
            # else:
            #     combined_notes = input_note_sequence
            # # print("Combined Notes after extending with EVENT_NOTE:", combined_notes)
            # combined_durations.extend(list(patterns[EVENT_DURATION]))
            # combined_amplitudes.extend(list(patterns[EVENT_AMPLITUDE]))
            # combined_gate.extend(list(patterns[EVENT_GATE]))
    # except ValueError as e:
    #         logging.error(f"Error reading {filename}: {e}")
            # continue
    
    
        # note_learner = MarkovLearner()
        # note_learner.learn_pattern(PSequence(combined_notes, 1))

        # dur_learner = MarkovLearner()
        # dur_learner.learn_pattern(PSequence(combined_durations, 1))

        # amp_learner = MarkovLearner()
        # amp_learner.learn_pattern(PInt(PRound(PScalar(PSequence(combined_amplitudes, 1)), -1)))
        
        # syllable_learner = MarkovLearner()
        # syllable_learner.learn_pattern(PSequence(combined_syllables, 1))
        
        # gate_learner = MarkovLearner()
        # gate_learner.learn_pattern(PSequence(combined_gate, 1))

        # # Generate Markov-based patterns for the section
    max_note_duration = 1.0
    if number_of_notes >= 13:
        print(f"number of notes is {number_of_notes} so we will reduce max_note_duration to 1/2")
        max_note_duration = 1/2
    min_note_duration = 1 / 2
        # note_pattern = PSubsequence(note_learner.markov, 0, number_of_notes)
    # detected_key = str(detected_key).replace("-", "")
    # enharmonic_key = key_signature.tonic.getEnharmonic()
    scale = Key(detected_key, detected_scale).scale
    note_pattern = PMap(note_markov, lambda note: quantize_to_scale(note, scale))
    duration_pattern = PMap(PSubsequence(dur_markov, 0, number_of_notes), lambda d: clamp(d, min_note_duration, max_note_duration))
    amplitude_pattern = PSubsequence(amp_markov, 0, number_of_notes)
        
        
        # Save section MIDI
    section_midi_path = f"outputs/sections/section_{bar_pair_name}.mid"
    midi_output = MidiFileOutputDevice(section_midi_path)
    timeline = Timeline(bpm, midi_output)
    timeline.stop_when_done = True
    timeline.schedule({
            "note": PSubsequence(note_pattern, 0, number_of_notes),
            "duration": PSubsequence(duration_pattern, 0, number_of_notes),
            "amplitude": PSubsequence(amplitude_pattern, 0, number_of_notes),
            "key": PSequence((detected_key, detected_scale))
            # "scale": PSequence([detected_scale], 1),
            # "gate": gate_pattern
        })

    try:
            logging.info(f"Generating and saving Section {bar_pair_name}... with number of notes {number_of_notes}")
            timeline.run()
            midi_output.write()
            time.sleep(1)
            # Print the section MIDI file size
            section_file_size = os.path.getsize(section_midi_path)
            logging.info(f"Section {bar_pair_name} saved to {section_midi_path}")
            logging.info(f"Section file size: {section_file_size} bytes")
            # Extract and print the sequence of notes in terms of pitch numbers
            try:
                section_midi = PrettyMIDI(section_midi_path)
                note_sequence = []
                for instrument in section_midi.instruments:
                    for note in instrument.notes:
                        note_sequence.append(note.pitch)
                
                if not note_sequence:
                    raise ValueError(f"Empty note sequence in section {bar_pair_name}. Please check the MIDI generation.")
                logging.info(f"Sequence of notes (pitch numbers) in section {bar_pair_name}: {note_sequence}")
            except Exception as e:
                logging.error(f"Error reading section MIDI file {section_midi_path}: {e}")
                
    except KeyboardInterrupt:
            timeline.output_device.all_notes_off()
            
  
    
def add_offset_to_section(
    section_path, output_path, start_bar, initial_gap_bars, bpm
):
    """
    Add an offset to a single sectional MIDI file based on its starting bar.

    Parameters:
    - section_path: Path to the input sectional MIDI file.
    - output_path: Path to save the offset-adjusted MIDI file.
    - start_bar: The starting bar for this section.
    - initial_gap_bars: Initial gap in bars to add at the beginning.
    - bpm: Beats per minute for timing calculations.
    """
    import pretty_midi
    from decimal import Decimal

    print(f"Processing section: {section_path}")
    print(f"Start bar: {start_bar}, Initial gap bars: {initial_gap_bars}, BPM: {bpm}")

    # Timing constants
    beat_duration = Decimal(60) / Decimal(bpm)
    bar_duration = beat_duration * 4  # 4 beats per bar

    # Calculate offset for this section in seconds
    offset_bars = Decimal(start_bar - 1) + Decimal(initial_gap_bars)
    offset_duration = offset_bars * bar_duration

    print(f"Calculated timing:")
    print(f" - Beat duration: {float(beat_duration):.4f} seconds")
    print(f" - Bar duration: {float(bar_duration):.4f} seconds")
    print(f" - Offset bars: {float(offset_bars):.2f} bars")
    print(f" - Offset duration: {float(offset_duration):.4f} seconds")

    # Load the section MIDI
    section_midi = pretty_midi.PrettyMIDI(section_path)
    print(f"Loaded MIDI file: {section_path}")

    # Apply offset to all notes, control changes, and pitch bends
    for instrument in section_midi.instruments:
        print(f"Adjusting notes for instrument: {instrument.name if instrument.name else 'Unknown Instrument'}")
        for note in instrument.notes:
            print(
                f"Note before offset: pitch={note.pitch}, "
                f"start={note.start:.4f}s, end={note.end:.4f}s"
            )
            note.start += float(offset_duration)
            note.end += float(offset_duration)
            print(
                f"Note after offset: pitch={note.pitch}, "
                f"start={note.start:.4f}s, end={note.end:.4f}s"
            )

        print("Adjusting control changes and pitch bends...")
        for cc in instrument.control_changes:
            print(f"Control Change before offset: number={cc.number}, time={cc.time:.4f}s")
            cc.time += float(offset_duration)
            print(f"Control Change after offset: number={cc.number}, time={cc.time:.4f}s")
        for pb in instrument.pitch_bends:
            print(f"Pitch Bend before offset: pitch={pb.pitch}, time={pb.time:.4f}s")
            pb.time += float(offset_duration)
            print(f"Pitch Bend after offset: pitch={pb.pitch}, time={pb.time:.4f}s")

    # Save the adjusted MIDI file
    section_midi.write(output_path)
    print(f"Offset added to {section_path}. New file saved as {output_path}.")
    print("-" * 50)




def combine_sectional_midis(
    input_folder, final_output_path, bpm
):
    """
    Combine all offset-adjusted sectional MIDI files into a single MIDI.

    Parameters:
    - input_folder: Folder containing the offset-adjusted sectional MIDI files.
    - final_output_path: Path to save the combined MIDI file.
    - bpm: Beats per minute for the combined MIDI.
    """
    import pretty_midi
    import os

    # Normalize paths
    input_folder = os.path.normpath(input_folder)
    final_output_path = os.path.normpath(final_output_path)

    # Create a PrettyMIDI object for the combined MIDI
    combined_midi = pretty_midi.PrettyMIDI()

    # Create a single instrument for the combined MIDI
    combined_instrument = pretty_midi.Instrument(program=0)  # Default: Acoustic Grand Piano

    # Load each MIDI file and add its notes to the combined instrument
    for midi_file in sorted(os.listdir(input_folder)):
        midi_path = os.path.join(input_folder, midi_file)
        section_midi = pretty_midi.PrettyMIDI(midi_path)

        for instrument in section_midi.instruments:
            combined_instrument.notes.extend(instrument.notes)
            combined_instrument.control_changes.extend(instrument.control_changes)
            combined_instrument.pitch_bends.extend(instrument.pitch_bends)

        print(f"Added {midi_file} to the final combined MIDI.")

    # Add the combined instrument to the PrettyMIDI object
    combined_midi.instruments.append(combined_instrument)

    # Save the final MIDI file
    combined_midi.write(final_output_path)
    print(f"Final combined MIDI saved to {final_output_path}.")

              
            

# def main(numer_of_notes, gap_positions, section_positions, reference_vocal_track, reference_octave, backing_analysis, vocal_analysis, consolidated_data, bpm=120):
    # some earier stuff  . . . 
#     current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
#     output_path = f"outputs/sections/generated_sequence_{current_time}.mid"
#     gap_output_path = f"outputs/sections/gap_generated_sequence_{current_time}.mid"
#     quantized_output_path = f"outputs/quantized_generated_sequence_{current_time}.mid"
#     final_output_path = f"outputs/generated_sequence_{current_time}.mid"
#     # Combine all sections into a single MIDI file
#     combine_sections(
#     output_folder="outputs/sections",
#     final_output_path=output_path,
#     bpm=120, 
#     initial_gap_beats=2,  # Adjust this value for the initial gap
#     section_gap_beats=2,  # Adjust this value for the gap between sections
#     ending_gap_beats=2    # Adjust this value for the ending gap
# )
#     add_gaps_to_midi(output_path, gap_output_path, gap_positions, bpm, 4)
#     quantize_note_durations(gap_output_path, quantized_output_path)
#     adjust_large_intervals_in_midi(quantized_output_path, final_output_path, detected_key+str(reference_octave))
    

   
def lyrics_time_calculation(
    output_folder="outputs/sections",
    bpm=120,
    input_text=None,
    initial_gap_bars=0,
    output_json_path="output_timing.json"
):
    """
    Calculate the timing for each sectional MIDI and associate it with the parsed lyrics.

    Parameters:
    - output_folder: Folder containing the sectional MIDI files.
    - bpm: Beats per minute for timing calculations.
    - input_text: String containing lyrics in the specified format.
    - initial_gap_bars: Initial gap in bars before the first section starts.
    - output_json_path: Path to save the final JSON output.

    Returns:
    - A JSON-like list of dictionaries with timing and lyric line associations.
    """
    import pretty_midi
    import os
    import re
    from decimal import Decimal
    import json

    if not input_text:
        raise ValueError("Input text with lyrics is required.")

    # Parse lyrics from input_text
    lyrics = [line.strip() for line in input_text.splitlines() if line.strip()]
    print(f"Parsed {len(lyrics)} lyric lines from input text: {lyrics}")

    # Normalize paths
    output_folder = os.path.normpath(output_folder)

    # Find section files matching the pattern
    pattern = re.compile(r"corrected_section_bar(\d+)-(\d+)\.mid")
    section_files = sorted(
        [f for f in os.listdir(output_folder) if pattern.match(f)],
        key=lambda x: int(re.search(r"(\d+)-", x).group(1))  # Sort by starting bar
    )

    # Timing constants
    beat_duration = Decimal(60) / Decimal(bpm)
    bar_duration = beat_duration * 4  # 4 beats per bar

    # Calculate timings and associate with lyrics
    result = []
    lyric_index = 0

    for section_file in section_files:
        # Extract starting and ending bars from the file name
        match = pattern.match(section_file)
        if not match:
            continue
        start_bar = int(match.group(1))
        end_bar = int(match.group(2))

        # Calculate offset in seconds
        offset_bars = Decimal(start_bar - 1) + Decimal(initial_gap_bars)
        offset_duration = offset_bars * bar_duration

        # Load the MIDI file and calculate section length
        section_path = os.path.join(output_folder, section_file)
        section_midi = pretty_midi.PrettyMIDI(section_path)

        # Calculate the duration of the section in seconds
        section_length_seconds = max(note.end for instrument in section_midi.instruments for note in instrument.notes)

        # Assign lyrics to the timing
        if lyric_index < len(lyrics):
            result.append({
                "line": lyrics[lyric_index],
                "startTime": float(offset_duration),
                "duration": float(section_length_seconds)
            })
            lyric_index += 1
        else:
            print(f"Warning: No more lyrics left to assign for section {section_file}. Skipping...")

        print(
            f"Section: {section_file}, Start Bar: {start_bar}, "
            f"Offset: {float(offset_duration):.2f}s, Duration: {float(section_length_seconds):.2f}s"
        )

    # Check if all lyrics were used
    if lyric_index < len(lyrics):
        print(f"Warning: Not all lyrics were assigned to sections. Remaining lines: {len(lyrics) - lyric_index}")

    # Save result to JSON file
    with open(output_json_path, "w") as json_file:
        json.dump(result, json_file, indent=4)
    print(f"Timing JSON saved to {output_json_path}.")

    # Output result as JSON string for reference
    json_output = json.dumps(result, indent=4)
    print("Generated timing JSON:")
    print(json_output)

    return result



def main_melody_generation(input_text, bpm, reference_backing_track, reference_vocal_track):

    # Process the input text
    # bpm = 115
    syllable_counts, total_syllables, line_level_total_syllables = calculate_syllable_counts(input_text)
    gap_positions = [line_level_total_syllables[0]]
    for idx in range(1, len(line_level_total_syllables)):
        new_value = gap_positions[idx-1] + line_level_total_syllables[idx]  # Sum of the current and previous element
        gap_positions.append(new_value)  
    

    # Print the result
    print(syllable_counts)
    print(total_syllables)
    print(line_level_total_syllables)
    print(gap_positions)


    # reference_backing_track = "C:/Users/divan/Downloads/Romania Track 1 - Chord Track - MIDI.mid"
    # reference_backing_track = "C:\\Users\\divan\\Downloads\\Germany-20241220T051109Z-001\\Germany\\Germany - Chord Tracks - MIDI\\Germany Track 8 - Chord Track - MIDI.mid"
    # reference_vocal_track = "C:\\Users\\divan\\Downloads\\MIDI x Untitled Production - Romania-20241210T150600Z-001\\MIDI x Untitled Production - Romania\\Romania Track 1 - MIDI.mid"
    # reference_vocal_track = "C:\\Users\\divan\\Downloads\\Germany-20241220T051109Z-001\\Germany\\Germany - Melody Tracks - MIDI\\Germany Track 8 - MIDI.mid"
    vocal_analysis = analyze_midi(reference_vocal_track, bpm)
    target_key = vocal_analysis["key"]
    # Analyze and transpose the backing track to match the vocal track's key
    backing_analysis = analyze_midi(reference_backing_track, bpm, True)
    print("backing track bar wise analysis")
    print(backing_analysis)
    print("vocal track bar wise analysis")
    print(vocal_analysis)
    
    consolidated_data = {
    "key": str(vocal_analysis["key"]),
    "bar_wise": {},
    "melodic_intervals": vocal_analysis["melodic_intervals"],
    "first_vocal_start": vocal_analysis["first_vocal_start"]
    }
    paired_data = group_bars_in_pairs(backing_analysis["bar_wise_chords"])
    print("paired_data  ", paired_data)
    progression_map = map_unique_progressions(paired_data)
    print("progression_map   ", progression_map)
    combined_progressions = combine_progressions(progression_map)
    print("combined_progressions   ", combined_progressions)
    vocal_activity = identify_vocal_activity(reference_vocal_track, bpm)
    print("vocal_activity   ", vocal_activity)
    filtered_progressions = filter_playing_progressions(combined_progressions, vocal_activity)
    print("Filtered Playing Progressions   ", filtered_progressions)
    # print(type(total_syllables), total_syllables)
    bar_pair_info = generate_bar_pair_info(filtered_progressions, line_level_total_syllables)
    print("bar_pair_info    ", bar_pair_info)
    length_of_filtered_progressions_map = len(filtered_progressions)
    number_of_unique_chord_progressions = length_of_filtered_progressions_map
    print("length_of_filtered_progressions_map  ", length_of_filtered_progressions_map)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_consolidated.json"
    print("consolidated_data  ")
    print(consolidated_data)
    original_midi_data = {}
    for chord_progression, bar_pairs in filtered_progressions.items():
        first_bar_pair = bar_pairs[0]
        # Generate the MIDI for this bar pair using markov_generation
        print(f"Generating MIDI for original bar pair: {first_bar_pair}")
        markov_generation(
        bar_pair_name=first_bar_pair,
        number_of_notes=bar_pair_info[first_bar_pair]['note_count'],
        reference_vocal_track=reference_vocal_track,
        reference_octave=4,
        backing_analysis=4,  # Example parameter, adjust as needed
        vocal_analysis=vocal_analysis,
        consolidated_data=consolidated_data,
        bpm=bpm
    )
        time.sleep(2)
        midi_file = f"/tmp/outputs/sections/section_{first_bar_pair}.mid"
        quantized_output_path = f"/tmp/outputs/sections/quantized_section_{first_bar_pair}.mid"
        octave_correction_output_path = f"/tmp/outputs/sections/octave_correction_section_{first_bar_pair}.mid"
        corrected_output_path = f"/tmp/outputs/sections/corrected_section_{first_bar_pair}.mid"
        quantize_note_durations(midi_file, quantized_output_path)
        
        time.sleep(2)
        bar_pair = first_bar_pair
        print("midi_file   ", midi_file)
        print("quantized_output_path    ", quantized_output_path)
        print("type of path is : ", type(quantized_output_path))
        try:
            print(f"Analyzing quantized MIDI: {quantized_output_path}")
            note_start_times = analyze_note_start_times(quantized_output_path)
            print(f"Note start times: {note_start_times}")
            
            for measure, notes in note_start_times.items():
                print(f"Measure {measure}:")
                for note_name, start_time in notes:
                    print(f"  Note {note_name} starts at {start_time} of the measure.")
            
            validation_report = validate_notes_against_chords(
                quantized_output_path, bar_pair, bar_pair_info, progression_map
            )
            print("validation_report   ", validation_report)
            
            for measure, issues in validation_report.items():
                print(f"Measure {measure}:")
                for note, start, expected in issues:
                    print(f"  Note {note} at {start} -> {expected}")
        
            # correct_midi_notes("outputs/sections/section_bar3-4.mid", "corrected_section_bar3-4.mid", ('A#2-major triad', 'C3-major triad', 'F2-major triad'), progression_map)
            for bar in set(backing_analysis["bar_wise_chords"].keys()).union(vocal_analysis["bar_wise_chords"].keys()):
                consolidated_data["bar_wise"][bar] = {
                    "backing_track_chords": backing_analysis["bar_wise_chords"].get(bar, []),
                    "vocal_chords": vocal_analysis["bar_wise_chords"].get(bar, []),
                    "pseudo_chords": backing_analysis["pseudo_chords"][bar - 1] if bar - 1 < len(backing_analysis["pseudo_chords"]) else []
                }
                
            # octave_normalization(quantized_output_path, 4, octave_correction_output_path)
            octave_normalization_with_two_octaves(quantized_output_path, 5, 4, octave_correction_output_path)
            correct_midi(
            midi_file=octave_correction_output_path,
            validation_report=validation_report,
            chord_map=chord_map,
            output_file=corrected_output_path
        )
            distance_based_octave_normalization(corrected_output_path, corrected_output_path)
            try: 
                print("codee reached here : ")
                # Store the melody structure in original_midi_data for reuse
                original_midi_data[chord_progression] = first_bar_pair
                print("original_midi_data[chord_progression]  ", original_midi_data[chord_progression] )
                
                # Mark the melody as generated for the first bar pair
                print("bar_pair_info[first_bar_pair] ", bar_pair_info[first_bar_pair])
                bar_pair_info[first_bar_pair]['melody_generated'] = True
                
                print("bar_pair_info ", bar_pair_info)
                
                # note_sequence = extract_note_sequence(corrected_output_path)
                # print("note_sequence ", note_sequence)
                
                update_bar_pair_info_with_note_sequence(bar_pair_info, first_bar_pair, corrected_output_path)
                
                print("bar_pair_info_after_changes  ", bar_pair_info)
                
            except Exception as e:
                        print(f"updating original midi data {quantized_output_path}: {e}")
            
            for bar_pair, info in bar_pair_info.items():
                if not info['melody_generated'] and 'note_sequence' in info:
                    print(f"Generating MIDI for bar pair: {bar_pair}")
                    
                    # Use note_sequence for Markov generation
                    note_sequence = info['note_sequence']
                    duration_sequence = info['duration_sequence']
                    amplitude_sequence = info['amplitude_sequence']
                    
                    last_bar = int(bar_pair.split('-')[-1])
                    # Extract valid notes for the last chord in the last bar
                    valid_notes = []
                    if last_bar in backing_analysis['combined_pseudo_chords']:
                        last_chord_info = backing_analysis['combined_pseudo_chords'][last_bar][-1]  # Last chord
                        valid_notes = last_chord_info[0]  # Extract pitch names
                        print(f"Valid notes for bar {last_bar} last chord: {valid_notes}")
                        
                    # Convert pitch names to MIDI numbers
                    chord_notes = [pitch_class_to_midi(pitch) for pitch in valid_notes]
                    print("chord_notes ", chord_notes)
                    if not chord_notes:  # Fallback if no valid notes are found
                        chord_notes = [60, 64, 67]  # Default to C major triad
                        print(f"No valid notes found for bar {last_bar}, defaulting to: {chord_notes}")
                    else:
                        chord_notes = adjust_to_octave_range(chord_notes, note_sequence)
                        print(f"Chord notes (MIDI numbers) for bar {last_bar}: {chord_notes}")

                    print("about to start generate_melody_with_chord")
                    # [65, 69, 72]      
                    generate_melody_with_chord(note_sequence, duration_sequence, amplitude_sequence, bar_pair_info[bar_pair]['note_count'], chord_notes, filename=f"/tmp/outputs/sections/section_{bar_pair}.mid")
                    
                    distance_based_octave_normalization(corrected_output_path, corrected_output_path)
                   
                    # generate_melody_with_chord(note_sequence, duration_sequence, amplitude_sequence, bar_pair_info[bar_pair]['note_count'], [65, 69, 72], filename=f"/tmp/outputs/sections/section_{bar_pair}.mid")

                    # Update the bar pair info to mark melody as generated
                    info['melody_generated'] = True

                    # Optional: Save or process the generated MIDI
                    repeating_midi_file = f"/tmp/outputs/sections/section_{bar_pair}.mid"
                    repeating_quantized_output_path = f"/tmp/outputs/sections/quantized_section_{bar_pair}.mid"
                    repeating_octave_correction_output_path = f"/tmp/outputs/sections/octave_correction_section_{bar_pair}.mid"
                    repeating_corrected_output_path = f"/tmp/outputs/sections/corrected_section_{bar_pair}.mid"
                    print(f"MIDI generated for {bar_pair}: {repeating_midi_file}")

                    # Simulate a delay for file saving
                    time.sleep(2)
                    quantize_note_durations(repeating_midi_file, repeating_quantized_output_path)
                    
                    time.sleep(2)
                    print("midi_file   ", repeating_midi_file)
                    print("quantized_output_path    ", repeating_quantized_output_path)
                    print("type of path is : ", type(repeating_quantized_output_path))
                    try:
                        print(f"Analyzing quantized MIDI: {repeating_quantized_output_path}")
                        note_start_times = analyze_note_start_times(repeating_quantized_output_path)
                        print(f"Note start times: {note_start_times}")
                        
                        for measure, notes in note_start_times.items():
                            print(f"Measure {measure}:")
                            for note_name, start_time in notes:
                                print(f"  Note {note_name} starts at {start_time} of the measure.")
                        
                        validation_report = validate_notes_against_chords(
                            repeating_quantized_output_path, bar_pair, bar_pair_info, progression_map
                        )
                        print("validation_report   ", validation_report)
                        
                        for measure, issues in validation_report.items():
                            print(f"Measure {measure}:")
                            for note, start, expected in issues:
                                print(f"  Note {note} at {start} -> {expected}")
                    
                        # correct_midi_notes("outputs/sections/section_bar3-4.mid", "corrected_section_bar3-4.mid", ('A#2-major triad', 'C3-major triad', 'F2-major triad'), progression_map)
                        for bar in set(backing_analysis["bar_wise_chords"].keys()).union(vocal_analysis["bar_wise_chords"].keys()):
                            consolidated_data["bar_wise"][bar] = {
                                "backing_track_chords": backing_analysis["bar_wise_chords"].get(bar, []),
                                "vocal_chords": vocal_analysis["bar_wise_chords"].get(bar, []),
                                "pseudo_chords": backing_analysis["pseudo_chords"][bar - 1] if bar - 1 < len(backing_analysis["pseudo_chords"]) else []
                            }
                        
                        # octave_normalization(repeating_quantized_output_path, 4, repeating_octave_correction_output_path)
                        octave_normalization_with_two_octaves(repeating_quantized_output_path, 5, 4, repeating_octave_correction_output_path)
                        correct_midi(
                        midi_file=repeating_octave_correction_output_path,
                        validation_report=validation_report,
                        chord_map=chord_map,
                        output_file=repeating_corrected_output_path
                    )

                        # Store the melody structure in original_midi_data for reuse
                        original_midi_data[chord_progression] = first_bar_pair

                        # Mark the melody as generated for the first bar pair
                        bar_pair_info[first_bar_pair]['melody_generated'] = True
                    except Exception as e:
                        print(f"Failed to analyze {quantized_output_path}: {e}")
                

            
            
        except Exception as e:
            print(f"Failed to analyze {quantized_output_path}: {e}")


    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"/tmp/outputs/sections/generated_sequence_{current_time}.mid"
    final_output_path = f"/tmp/outputs/generated_sequence_{current_time}.mid"
    starting_offset = vocal_analysis["first_vocal_start"]["time"]
    print("starting_offset  ", starting_offset)
    if starting_offset == None: 
        starting_offset = 0
        
    pattern = re.compile(r"corrected_section_bar(\d+)-\d+\.mid")

    # Step 1: Add offsets to each sectional MIDI
    for section_file in os.listdir("/tmp/outputs/sections"):
        match = pattern.match(section_file)
        if not match:
            continue

        start_bar = int(match.group(1))
        section_path = os.path.join("/tmp/outputs/sections", section_file)
        output_path = os.path.join("/tmp/outputs/adjusted_sections", section_file)

        add_offset_to_section(
            section_path=section_path,
            output_path=output_path,
            start_bar=start_bar,
            initial_gap_bars=0,
            bpm=120
        )

    # Step 2: Combine all offset-adjusted MIDIs
    combine_sectional_midis(
        input_folder="/tmp/outputs/adjusted_sections",
        final_output_path=final_output_path,
        bpm=bpm
    )
    # combine_sections(
    #                 output_folder="/tmp/outputs/sections",
    #                 final_output_path=output_path,
    #                 bpm=bpm, 
    #                 initial_gap_beats=starting_offset,  # Adjust this value for the initial gap
    #                 section_gap_beats=2,  # Adjust this value for the gap between sections
    #                 ending_gap_beats=7    # Adjust this value for the ending gap
    #             )  
    shutil.copy(final_output_path, "/tmp/midi.mid")
    # detected_key = vocal_analysis["key"].tonic.name
    # detected_scale = vocal_analysis["key"].mode
    # reference_octave = 4
    # adjust_large_intervals_in_midi(output_path, final_output_path, detected_key+str(reference_octave))
    

    print("========================================================================================================")


if __name__ == "__main__":
    # Example input
    lyrics="""
    Sofia + du bist wunderbar + + +
    Ein Lächeln + so hell und klar +
    Danke + für all die schönen + Stunden +
    Mit dir wird Freude + immer + gefunden + +
    Danke + sage + ich dir von Herzen +
    Für all die Liebe + all die Schmerzen +
    Du bist immer + für mich da
    Ein Freund + so nah so wunderbar + + +
    In Hamburg + + an der Elbe + so weit
    Erinnern + + wir uns an die schöne + Zeit
    Sofia + du bist ein wahrer + Schatz
    Gefüllt + mit Liebe + ohne + Matsch
    """
    reference_backing_track = "C:/Users/divan/Downloads/Romania Track 1 - Chord Track - MIDI.mid"
    # reference_backing_track = "C:\\Users\\divan\\Downloads\\Germany-20241220T051109Z-001\\Germany\\Germany - Chord Tracks - MIDI\\GermanyTrack1ChordMIDI.mid"
    reference_vocal_track = "C:\\Users\\divan\\Downloads\\MIDI x Untitled Production - Romania-20241210T150600Z-001\\MIDI x Untitled Production - Romania\\Romania Track 1 - MIDI.mid"
    # reference_vocal_track = "C:\\Users\\divan\\Downloads\\Germany-20241220T051109Z-001\\Germany\\Germany - Melody Tracks - MIDI\\GermanyTrack1MIDI.mid"
    main_melody_generation(lyrics, 115, reference_backing_track, reference_vocal_track)