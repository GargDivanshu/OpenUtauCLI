import re
import pretty_midi
import os
from datetime import datetime
from lyrics_el import process_ballad_lyrics

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
    Count the total syllables in a given lyric line by considering words and '+' signs.
    
    Parameters:
    - line: The lyric line to analyze.

    Returns:
    - Total syllable count.
    """
    # Find all words and '+' signs
    words = re.findall(r'\b\w+\b', line)  # Extracts words
    plus_signs = line.count('+')  # Counts '+' occurrences

    total_syllables = len(words) + plus_signs  # Syllables = Words + Number of '+'
    return total_syllables



def adjust_lyrics_to_midi(lyrics, midi_folder, output_folder="generations", bpm=120):
    """
    Adjust lyrics based on the number of notes in corresponding MIDI files and save adjusted versions
    to a separate folder.

    Parameters:
    - lyrics: List of formatted lyric lines.
    - midi_folder: Path to the folder containing section MIDI files.
    - output_folder: Path to save the modified MIDI files.
    - bpm: Beats per minute for calculating note durations.

    Returns:
    - Adjusted lyrics where syllable counts (words + '+' signs) match the note count in corresponding MIDI files.
    """

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

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

        if num_syllables < num_notes:
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

    print("\nFinal adjusted lyrics:")
    for line in adjusted_lyrics:
        print(line)

    return adjusted_lyrics







if __name__ == "__main__":
    input_lyrics = """
    Η σιωπή + σου με ξυπνάει +
    Μες της νύχτας + το κενό +
    Και ο χρόνος που κυλάει +
    Πιο μακριά + σε παρασέρνει + + + την αγάπη μας σκορπάει +
    Και φωνάζω + στις πλατείες + + το όνομα + σου μα κενό +
    Χάνομαι + μέσα στις μνήμες + που ακόμη αγαπώ +
    Ένα χάδι ένα φιλί + σου ένα βλέμμα + είν' + αρκετό + + Για να αφήσω + ότι έχω
    και να έρθω + να σε βρω
    """

    print("\nProcessing initial lyrics...\n")
    formatted_lyrics = process_ballad_lyrics(input_lyrics)
    adjusted_lyrics = adjust_lyrics_to_midi(formatted_lyrics, "outputs/greek_track1_sections", "outputs/greek_track1_sections/generations")

    input_folder = "outputs/greek_track1_sections"
    output_folder = "outputs"
    final_midi_path = combine_sectional_midis(input_folder, output_folder)

    print(f"\nGenerated final MIDI: {final_midi_path}")
