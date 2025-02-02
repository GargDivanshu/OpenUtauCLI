import openai
import os
import re
import pyphen

# Initialize Pyphen for German syllabification
syllable_splitter = pyphen.Pyphen(lang='hu_HU')


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
        "A magyar nyelvben minden szótag legalább egy magánhangzót kell tartalmazzon (a, e, i, o, ö, u, ü, á, é, í, ó, ő, ú, ű). A magyarban nincsenek kettőshangzók (diftongusok), így minden magánhangzó külön szótagot alkot. Például: poéta (költő) → po-é-ta(3)."
        "A szótagok száma egyenlő a szóban található magánhangzók számával. Például: asztal (asztal) → asz-tal(2), szerelem (szerelem) → sze-re-lem(3)."
        "Ha több mássalhangzó szerepel két magánhangzó között, akkor a szótaghatár általában az utolsó mássalhangzó előtt van. Például: okos (okos) → o-kos(2), képzelet (képzelet) → kép-ze-let(3)."
        "Ha egyetlen mássalhangzó áll két magánhangzó között, az a következő szótagba kerül. Például: elefánt (elefánt) → e-le-fánt(3)."
        "Ha egy szó kettős mássalhangzót tartalmaz (pl. tt, ss, zz), akkor az szótagoláskor különválik. Például: hosszú (hosszú) → hosz-szú(2)."
        "Az elöljárók és előtagok külön szótagot alkotnak. Például: megszólal (megszólal) → meg-szó-lal(3)."
        "Összetett szavaknál minden komponens megtartja saját szótagolási szabályait. Például: kézitáska (kézitáska) → ké-zi-tás-ka(4)."
        "A magyar hangsúly minden szó első szótagjára esik, ezt szigorúan be kell tartani. A soronkénti szótagok számának pontosnak kell lennie, a természetes ritmus megtartásával, torzítás nélkül."
        "A beszélt magyarban bizonyos szavak összeolvadnak, de a helyes szótagolásnál minden szónak meg kell tartania saját szótagstruktúráját. Például: nevetek (nevetek) → ne-ve-tek(3), do autó (autóba) → do au-tó(3)."
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

# lyrics = """
# A szeretetet, a fájdalmat, mindenből.
# """
# print(analyze_lyrics(lyrics))