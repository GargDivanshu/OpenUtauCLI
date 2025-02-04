import shutil
from greek_ballad import combine_sectional_midis, adjust_lyrics_to_midi_with_track


lyrics = """
Καθισμένος + + + στο γραφείο + +
Η καρδιά + μου δε χτυπά +
Μα είναι + κάτι + μαγικό + +
Γύρω + τις ματιές + σου πάντα + η αγάπη + + με καλεί +
Το χαμόγελο + + + σου φεύγει + σαν το τρέχω + να το πω
Είσαι + εσύ + αγαπημένε + + + + άνοιξα + + σαν με κοιτώ +
Με ένα + γέλιο + μια αγκαλιά + + σου ξεχνώ + κάθε + καημό + να σου λέω + μυστικά + + που
Πάντα + σε αγαπώ + +
"""


midi_folder = "greek_track2_sections"
output_folder = "greek_track2_sections/generations"
formatted_lyrics = adjust_lyrics_to_midi_with_track(lyrics, midi_folder, output_folder, [9, 9, 9, 19, 19, 18, 27, 9])
print("received back -->")
print(formatted_lyrics)
output_file = "lyrics.txt"
with open(output_file, "w", encoding="utf-8") as file:
            file.write(formatted_lyrics)
input_folder = "greek_track2_sections"
final_midi_path = combine_sectional_midis(input_folder, "outputs")
shutil.copy(final_midi_path, "midi.mid")
