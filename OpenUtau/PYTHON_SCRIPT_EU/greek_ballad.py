import re
import pretty_midi
import os
from datetime import datetime
from lyrics_el import process_ballad_lyrics


def lyrics_timing_for_sections(
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
    if not input_text:
        raise ValueError("Input text with lyrics is required.")

    import pretty_midi
    import os
    import re
    import json
    from decimal import Decimal

    # Parse lyrics from input_text
    lyrics = [line.strip() for line in input_text.splitlines() if line.strip()]
    print(f"Parsed {len(lyrics)} lyric lines from input text: {lyrics}")

    # Normalize paths
    output_folder = os.path.normpath(output_folder)

    # Find section files matching the pattern (e.g., section_1.mid, section_2.mid)
    pattern = re.compile(r"section_(\d+)\.mid")
    section_files = sorted(
        [f for f in os.listdir(output_folder) if pattern.match(f)],
        key=lambda x: int(pattern.match(x).group(1))
    )

    if not section_files:
        raise FileNotFoundError(f"No section MIDI files found in {output_folder}")

    # Timing constants
    beat_duration = Decimal(60) / Decimal(bpm)
    bar_duration = beat_duration * 4  # 4 beats per bar

    # Calculate timings and associate with lyrics
    result = []
    current_start_time = Decimal(initial_gap_bars) * bar_duration

    for index, section_file in enumerate(section_files):
        section_path = os.path.join(output_folder, section_file)

        # Load the MIDI file and calculate section length
        section_midi = pretty_midi.PrettyMIDI(section_path)
        section_duration = max(note.end for instrument in section_midi.instruments for note in instrument.notes)

        # Assign lyrics to the timing
        if index < len(lyrics):
            result.append({
                "line": lyrics[index],
                "startTime": float(current_start_time),
                "duration": float(section_duration),
                "file": section_file
            })
        else:
            print(f"Warning: No more lyrics left to assign for section {section_file}. Skipping...")

        print(
            f"Section: {section_file}, Start Time: {float(current_start_time):.2f}s, "
            f"Duration: {float(section_duration):.2f}s"
        )

        # Increment the start time for the next section
        current_start_time += Decimal(section_duration)

    # Check if all lyrics were used
    if len(result) < len(lyrics):
        print(f"Warning: Not all lyrics were assigned to sections. Remaining lines: {len(lyrics) - len(result)}")

    # Save result to JSON file with UTF-8 encoding and ensure_ascii=False
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4, ensure_ascii=False)
    print(f"Timing JSON saved to {output_json_path}.")

    # Output result as JSON string for reference with correct encoding
    json_output = json.dumps(result, indent=4, ensure_ascii=False)
    print("Generated timing JSON:")
    print(json_output)

    return result



def lyrics_timing_for_track2(
    output_folder="outputs/sections",
    input_text=None,
    output_json_path="output_timing_fixed.json"
):
    """
    Associate fixed start times and durations with the parsed lyrics.

    Parameters:
    - output_folder: Folder containing the sectional MIDI files.
    - input_text: String containing lyrics in the specified format.
    - output_json_path: Path to save the final JSON output.

    Returns:
    - A JSON-like list of dictionaries with fixed timing and lyric line associations.
    """
    if not input_text:
        raise ValueError("Input text with lyrics is required.")

    import os
    import re
    import json

    # Parse lyrics from input_text
    lyrics = [line.strip() for line in input_text.splitlines() if line.strip()]
    print(f"Parsed {len(lyrics)} lyric lines from input text: {lyrics}")

    # Predefined start times and durations
    fixed_timings = [
        (3.3, 3.4),
        (10.0, 3.4),
        (16.7, 3.4),
        (22.67, 5.1),
        (30.0, 5.4),
        (36.8, 6.4),
        (44, 10.0),
        (54.5, 2.5)
    ]

    # Check if provided lyrics match the number of fixed timings
    if len(lyrics) > len(fixed_timings):
        raise ValueError(f"More lyrics provided ({len(lyrics)}) than available fixed timings ({len(fixed_timings)})")

    # Normalize paths
    output_folder = os.path.normpath(output_folder)

    # Find section files matching the pattern (e.g., section_1.mid, section_2.mid)
    pattern = re.compile(r"section_(\d+)\.mid")
    section_files = sorted(
        [f for f in os.listdir(output_folder) if pattern.match(f)],
        key=lambda x: int(pattern.match(x).group(1))
    )

    if not section_files:
        raise FileNotFoundError(f"No section MIDI files found in {output_folder}")

    result = []
    for index, (start_time, duration) in enumerate(fixed_timings):
        if index < len(lyrics):
            result.append({
                "line": lyrics[index],
                "startTime": start_time,
                "duration": duration,
                "file": section_files[index] if index < len(section_files) else None
            })
        else:
            print(f"Warning: No more lyrics left to assign for section {section_files[index]}. Skipping...")

        print(
            f"Section: {section_files[index]}, Start Time: {start_time:.2f}s, "
            f"Duration: {duration:.2f}s"
        )

    # Save result to JSON file with UTF-8 encoding and ensure_ascii=False
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4, ensure_ascii=False)
    print(f"Timing JSON saved to {output_json_path}.")

    # Output result as JSON string for reference with correct encoding
    json_output = json.dumps(result, indent=4, ensure_ascii=False)
    print("Generated timing JSON:")
    print(json_output)

    return result


def lyrics_timing_for_track3(
    output_folder="outputs/sections",
    input_text=None,
    output_json_path="output_timing_fixed.json"
):
    """
    Associate fixed start times and durations with the parsed lyrics.

    Parameters:
    - output_folder: Folder containing the sectional MIDI files.
    - input_text: String containing lyrics in the specified format.
    - output_json_path: Path to save the final JSON output.

    Returns:
    - A JSON-like list of dictionaries with fixed timing and lyric line associations.
    """
    if not input_text:
        raise ValueError("Input text with lyrics is required.")

    import os
    import re
    import json

    # Parse lyrics from input_text
    lyrics = [line.strip() for line in input_text.splitlines() if line.strip()]
    print(f"Parsed {len(lyrics)} lyric lines from input text: {lyrics}")

    # Predefined start times and durations
    fixed_timings = [
        (9.1, 2.6),
        (12.6, 2.8),
        (17.2, 7.2),
        (25.5, 7.5),
        (33.8, 7.4),
        (42.1, 7.4),
        (50.4, 7.0),
    ]

    # Check if provided lyrics match the number of fixed timings
    if len(lyrics) > len(fixed_timings):
        raise ValueError(f"More lyrics provided ({len(lyrics)}) than available fixed timings ({len(fixed_timings)})")

    # Normalize paths
    output_folder = os.path.normpath(output_folder)

    # Find section files matching the pattern (e.g., section_1.mid, section_2.mid)
    pattern = re.compile(r"section_(\d+)\.mid")
    section_files = sorted(
        [f for f in os.listdir(output_folder) if pattern.match(f)],
        key=lambda x: int(pattern.match(x).group(1))
    )

    if not section_files:
        raise FileNotFoundError(f"No section MIDI files found in {output_folder}")

    result = []
    for index, (start_time, duration) in enumerate(fixed_timings):
        if index < len(lyrics):
            result.append({
                "line": lyrics[index],
                "startTime": start_time,
                "duration": duration,
                "file": section_files[index] if index < len(section_files) else None
            })
        else:
            print(f"Warning: No more lyrics left to assign for section {section_files[index]}. Skipping...")

        print(
            f"Section: {section_files[index]}, Start Time: {start_time:.2f}s, "
            f"Duration: {duration:.2f}s"
        )

    # Save result to JSON file with UTF-8 encoding and ensure_ascii=False
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4, ensure_ascii=False)
    print(f"Timing JSON saved to {output_json_path}.")

    # Output result as JSON string for reference with correct encoding
    json_output = json.dumps(result, indent=4, ensure_ascii=False)
    print("Generated timing JSON:")
    print(json_output)

    return result



def combine_sectional_midis(input_folder, output_folder):
    """
    Combine all sectional MIDI files in the input folder into a single MIDI file.

    Parameters:
    - input_folder: Folder containing the sectional MIDI files.
    - output_folder: Folder to save the combined MIDI file.

    Returns:
    - The path to the final combined MIDI file.
    """

    # Get the current datetime for naming the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_output_path = os.path.join(output_folder, f"generated_sequence_{timestamp}.mid")

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Create a PrettyMIDI object for the combined MIDI
    combined_midi = pretty_midi.PrettyMIDI()

    # Create a single instrument for the combined MIDI
    combined_instrument = pretty_midi.Instrument(program=0)  # Default to Acoustic Grand Piano

    # Load each MIDI file and add its notes to the combined instrument
    midi_files = sorted(
        [f for f in os.listdir(input_folder) if f.endswith(".mid")],
        key=lambda x: int(re.search(r"section_(\d+)", x).group(1)) if re.search(r"section_(\d+)", x) else 0
    )

    if not midi_files:
        raise ValueError(f"No MIDI files found in {input_folder}")

    print(f"Combining {len(midi_files)} MIDI files...")

    for midi_file in midi_files:
        midi_path = os.path.join(input_folder, midi_file)
        try:
            section_midi = pretty_midi.PrettyMIDI(midi_path)
            for instrument in section_midi.instruments:
                combined_instrument.notes.extend(instrument.notes)
                combined_instrument.control_changes.extend(instrument.control_changes)
                combined_instrument.pitch_bends.extend(instrument.pitch_bends)
            print(f"Added {midi_file} to the final combined MIDI.")
        except Exception as e:
            print(f"Error processing {midi_file}: {e}")

    # Add the combined instrument to the PrettyMIDI object
    combined_midi.instruments.append(combined_instrument)

    # Save the final MIDI file
    combined_midi.write(final_output_path)
    print(f"Final combined MIDI saved as {final_output_path}")

    return final_output_path



import shutil
import pretty_midi
import os
import re


def count_syllables(line):
    """
    Count the number of syllables in a line.

    Syllables are defined as:
    - One per word.
    - One for each '+' sign.

    Parameters:
    - line: A single line of lyrics.

    Returns:
    - Integer count of syllables in the line.
    """
    words = line.split()  # Split into words
    syllable_count = 0

    for word in words:
        # Count the base word as one syllable
        syllable_count += 1
        # Count '+' signs in the word as additional syllables
        # syllable_count += word.count('+')

    return syllable_count




def adjust_lyrics_to_midi(lyrics_input, midi_folder, output_folder="generations", bpm=120):
    if isinstance(lyrics_input, tuple):
        lyrics_str = lyrics_input[0]  # Extract the string part
    else:
        lyrics_str = lyrics_input

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Split lyrics into lines
    lyrics = lyrics_str.strip().split("\n")

    adjusted_lyrics = []
    beat_duration = 60 / bpm  # Calculate 1 beat duration in seconds
    half_bar_duration = beat_duration * 2  # 2 beats = half bar (assuming 4/4 time)

    print("\nAdjusting lyrics to match MIDI notes:")

    for index, line in enumerate(lyrics, start=1):
        # Count syllables using the updated function
        num_syllables = count_syllables(line)

        # Load corresponding MIDI file
        midi_filename = f"section_{index}.mid"
        midi_path = os.path.join(midi_folder, midi_filename)
        output_midi_path = os.path.join(output_folder, midi_filename)

        if not os.path.exists(midi_path):
            raise FileNotFoundError(f"MIDI file {midi_path} not found.")

        midi_data = pretty_midi.PrettyMIDI(midi_path)

        # Count number of notes in the MIDI
        num_notes = sum(len(instrument.notes) for instrument in midi_data.instruments)

        print(f"Processing {midi_filename}: Lyrics syllables: {num_syllables}, MIDI notes: {num_notes}")

        if num_syllables <= num_notes:
            # Add "+" to words evenly across the line to match note count
            difference = num_notes - num_syllables
            words = line.split()
            for i in range(difference):
                words[i % len(words)] += " +"
            line = " ".join(words)
            print(f"Updated lyrics (added +): {line}")

            # Copy the original MIDI file to the generations folder
            shutil.copy(midi_path, output_midi_path)
            print(f"No MIDI changes. Copied original to: {output_midi_path}")

        elif num_syllables > num_notes:
            # Add extra half-bar length notes at the end to match the syllable count
            last_note = midi_data.instruments[0].notes[-1]  # Get the last note
            start_time = last_note.end

            for _ in range(num_syllables - num_notes):
                new_note = pretty_midi.Note(
                    velocity=last_note.velocity,
                    pitch=last_note.pitch,
                    start=start_time,
                    end=start_time + half_bar_duration  # Half bar duration
                )
                midi_data.instruments[0].notes.append(new_note)
                start_time = new_note.end  # Move start time for next note

            # Save adjusted MIDI to the generations folder
            midi_data.write(output_midi_path)
            print(f"Updated MIDI (added notes) saved to: {output_midi_path}")

        else:
            # Always copy the original MIDI to the generations folder if no changes
            shutil.copy(midi_path, output_midi_path)
            print(f"No changes needed. Copied original MIDI to: {output_midi_path}")

        adjusted_lyrics.append(line)

    # Convert adjusted lyrics back to a multiline string
    adjusted_lyrics_str = "\n".join(adjusted_lyrics)

    print("\nFinal adjusted lyrics:\n")
    print(adjusted_lyrics_str)

    return adjusted_lyrics_str


def adjust_lyrics_to_midi_with_track(lyrics_input, midi_folder, output_folder="generations", track_notes=None, bpm=120):
    if isinstance(lyrics_input, tuple):
        lyrics_str = lyrics_input[0]  # Extract the string part
    else:
        lyrics_str = lyrics_input

    if track_notes is None:
        raise ValueError("The track_notes array must be provided.")

    # Print input data
    print(f"Input lyrics:\n{lyrics_str}")
    print(f"Track notes: {track_notes}")

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Split lyrics into lines
    lyrics = lyrics_str.strip().split("\n")

    # Print number of lines and notes alignment
    print(f"Number of lyric lines: {len(lyrics)}")
    print(f"Number of track notes: {len(track_notes)}")

    if len(lyrics) != len(track_notes):
        raise ValueError(f"The number of lines in lyrics ({len(lyrics)}) does not match the length of track_notes ({len(track_notes)}).")

    adjusted_lyrics = []
    beat_duration = 60 / bpm  # Calculate 1 beat duration in seconds

    print("\nAdjusting lyrics to match predefined track notes:")

    for index, (line, intended_notes) in enumerate(zip(lyrics, track_notes), start=1):
        # Count syllables in the line (words + '+' signs)
        # num_syllables = sum(len(word.split('+')) for word in line.split())
        num_syllables = count_syllables(line)

        # Print line details
        print(f"Processing line {index}:")
        print(f"Original line: {line}")
        print(f"Number of syllables in line: {num_syllables}")
        print(f"Intended notes: {intended_notes}")

        if num_syllables < intended_notes:
            print(f"Line {index} has {num_syllables} syllables but needs {intended_notes}. Adding {intended_notes - num_syllables} '+' signs.")
            difference = intended_notes - num_syllables

            # Split the line into words
            words = line.split()

            # Find the positions of the existing "+" signs
            plus_positions = []
            for i, word in enumerate(words):
                if "+" in word:
                    plus_positions.append(i)

            # If there are no "+" signs, treat the first word as the starting point
            if not plus_positions:
                # If there are no existing "+" signs, add "+" signs at the end
                for _ in range(difference):
                    words.append("+")

            # Distribute the "+" signs after existing "+" positions
            for i in range(difference):
                # Calculate the position to insert the new "+"
                insert_pos = plus_positions[i % len(plus_positions)]
                # Add a "+" to the appropriate word
                words[insert_pos] += " +"

            # Reconstruct the line
            line = " ".join(words)
            print(f"Updated line: {line}")


        # Load corresponding MIDI file
        midi_filename = f"section_{index}.mid"
        midi_path = os.path.join(midi_folder, midi_filename)
        output_midi_path = os.path.join(output_folder, midi_filename)

        print(f"Loading MIDI file: {midi_filename} from {midi_path}")
        if not os.path.exists(midi_path):
            print(f"Error: MIDI file {midi_filename} does not exist!")
            raise FileNotFoundError(f"MIDI file {midi_path} not found.")
        else:
            print(f"MIDI file {midi_filename} loaded successfully.")

        midi_data = pretty_midi.PrettyMIDI(midi_path)

        # Copy the original MIDI file to the generations folder (no modifications to MIDI here)
        shutil.copy(midi_path, output_midi_path)
        print(f"No MIDI changes. Copied original to: {output_midi_path}")

        adjusted_lyrics.append(line)
        print(f"Final adjusted line {index}: {line}")

    # Convert adjusted lyrics back to a multiline string
    adjusted_lyrics_str = "\n".join(adjusted_lyrics)

    print("\nFinal adjusted lyrics:\n")
    print(adjusted_lyrics_str)

    return adjusted_lyrics_str
