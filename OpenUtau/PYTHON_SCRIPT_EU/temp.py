import shutil
from lyrics_el import process_ballad_lyrics
from greek_ballad import adjust_lyrics_to_midi, combine_sectional_midis, lyrics_timing_for_sections, lyrics_timing_for_track2
from lyrics import analyze_lyrics_de, analyze_lyrics_ro, analyze_lyrics_hu, analyze_lyrics_cs, analyze_lyrics_sk, analyze_lyrics_el, analyze_lyrics_es


lyrics = """
Η καφέ σου μυρωδιά 
Μέσα στο γραφείο γλυκιά, 
Και το βλέμμα σου γελάει, 
Μια κουβέντα σου μ’ αγγίζει, την καρδιά μου ζεσταίνει ξανά. 
Και σε βλέπω στο πρωί, Γιώργο, πάντα μ’ ένα χαμόγελο, 
Ο καφές που μου προσφέρεις, δείχνει πόσο σ’ αγαπώ. 
Ένα βλέμμα, ευγένεια σου, μου αρκεί καθε μερά, Στην δουλειά μας φωτίζεις
και είναι όλα μαγικά!
"""

# lyrics, lyrics_as_list = process_ballad_lyrics(lyrics)
formatted_lyrics = analyze_lyrics_el(lyrics)
print(lyrics)
print(formatted_lyrics)
print(type(formatted_lyrics))


midi_folder = "greek_track2_sections"
output_folder = "greek_track2_sections/generations"
formatted_lyrics = adjust_lyrics_to_midi(formatted_lyrics, midi_folder, output_folder)
output_file = "lyrics.txt"
with open(output_file, "w", encoding="utf-8") as file:
            file.write(formatted_lyrics)
input_folder = "greek_track2_sections"
final_midi_path = combine_sectional_midis(input_folder, "outputs")
shutil.copy(final_midi_path, "midi.mid")