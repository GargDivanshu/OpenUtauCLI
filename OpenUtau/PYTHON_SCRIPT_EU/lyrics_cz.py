import openai
import os
import re
import pyphen


# Initialize Pyphen for Romanian syllabification
syllable_splitter = pyphen.Pyphen(lang='cs_CZ')

# Choose method: "PYPHEN" or "OPENAI"
# SYLLABLE_METHOD = "OPENAI"  # Change to "OPENAI" to use GPT

def call_gpt_for_syllables(lyrics):
    """
    Call GPT-4o API to analyze and return syllable counts for each word in the lyrics.

    Parameters:
    - lyrics: Multi-line string of lyrics.

    Returns:
    - GPT response containing syllabified words in the format "word(syllable_count)"
    """
    prompt = (
        "You will be given a line of lyrics. For each word, return the word followed by its syllable count "
        "in the format: word(syllable_count). Ensure each syllable count is accurate.\n\n"
        f"Lyrics line: \"{lyrics}\"\n"
        "Return the formatted output in one line, like: word1(2) word2(1) word3(3) ... "
        "V češtině musí každá slabika obsahovat alespoň jednu samohlásku (a, e, i, o, u, y, á, é, í, ó, ú, ý), přičemž dvojhlásky (au, eu, ou) se počítají jako jedna slabika."
        "Slabikotvorné souhlásky r a l mohou v určitých případech fungovat jako samohlásky a tvořit samostatnou slabiku, pokud za nimi nenásleduje další samohláska. Například: vlk (vlk) → vlk(1), krk (krk) → krk(1), prst (prst) → prst(1). Pokud je však za nimi samohláska, nejsou slabikotvorné, například ro-la(2) místo rla(1)."
        "Když se mezi samohláskami vyskytuje více souhlásek, dělení obvykle probíhá před poslední souhláskou ve skupině. Například: okno (okno) → ok-no(2), sestra (sestra) → ses-tra(2)."
        "Výjimkou jsou případy, kdy souhlásková skupina tvoří známou kombinaci (bl, pl, pr, br, tr, kr, kl, dr, gr), která zůstává pohromadě. Například: matka (matka) → mat-ka(2), stopa (stopa) → sto-pa(2)."
        "Slova s předponami si zachovávají předponu jako samostatnou část. Například: odjet (odjet) → od-jet(2), představovat (představovat) → před-sta-vo-vat(4)."
        "Dvě po sobě jdoucí samohlásky se nespojí do jedné slabiky, pokud netvoří dvojhlásku. Například: poezie (poezie) → po-e-zi-e(4). Pokud se i nebo y nachází za souhláskou a před další samohláskou, zůstává samostatnou slabikou, například dívka (dívka) → dív-ka(2)."
        "V mluvené češtině se některá slova mohou spojovat, ale ve správném slabikování musí každé slovo zachovat svůj správný počet slabik. Například: nechci (nechci) → nech-ci(2), do auta (do auta) → do au-ta(3)."
        "Be intelligent when assigning syllables. Only generate the lyrics and no other commentary."
    )


    client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
    # client = openai.Client(api_key="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")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert in Greek phonetics."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    return response.choices[0].message.content.strip()

def parse_gpt_response(gpt_response):
    """
    Parse the GPT response to extract words and their syllable counts.

    Parameters:
    - gpt_response: The GPT output containing words with syllable counts.

    Returns:
    - A list of tuples (word, syllable_count).
    """
    pattern = re.compile(r"(\w+)\((\d+)\)")
    matches = pattern.findall(gpt_response)

    syllable_info = [(word, int(count)) for word, count in matches]
    return syllable_info

def count_syllables_pyphen(word):
    """Count the number of syllables in a word using Pyphen."""
    syllables = syllable_splitter.inserted(word)
    return len(syllables.split('-')), syllables

def format_line_in_utau(lyrics, syllable_method="OPENAI"):
    """
    Format lyrics into OpenUTAU format based on syllable counts.
    
    Parameters:
    - lyrics: Lyrics string.

    Returns:
    - Formatted lyrics string.
    """
    if syllable_method == "OPENAI":
        gpt_response = call_gpt_for_syllables(lyrics)
        syllable_info = parse_gpt_response(gpt_response)
    else:
        words = lyrics.split()
        syllable_info = [(word, count_syllables_pyphen(word)[0]) for word in words]

    formatted_words = []
    for word, syllable_count in syllable_info:
        if syllable_count > 1:
            formatted_word = f"{word} {'+ ' * (syllable_count - 1)}".strip()
            formatted_words.append(formatted_word)
        else:
            formatted_words.append(word)

    return ' '.join(formatted_words)

def analyze_lyrics(lyrics, syllable_method):
    """
    Analyze lyrics for syllable breakdown and OpenUTAU formatting.

    Parameters:
    - lyrics: Multi-line lyrics as input.

    Returns:
    - Formatted lyrics.
    """
    lines = lyrics.strip().split('\n')
    formatted_lines = []

    for line in lines:
        formatted_line = format_line_in_utau(line, syllable_method)
        formatted_lines.append(formatted_line)

    return '\n'.join(formatted_lines)