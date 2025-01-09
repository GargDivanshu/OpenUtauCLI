import pyphen

# Initialize Pyphen for German syllabification
syllable_splitter = pyphen.Pyphen(lang='de_DE')

def count_syllables(word):
    """Count the number of syllables in a word using Pyphen."""
    syllables = syllable_splitter.inserted(word)
    return len(syllables.split('-')), syllables

def format_line_in_utau(line):
    """
    Format a line into OpenUTAU format by adding + after multisyllabic words.
    Args:
        line (str): A line of lyrics.
    Returns:
        tuple: Formatted line in OpenUTAU-compatible format and syllable breakdown.
    """
    # Remove commas and periods from the line
    line = line.replace(',', '').replace('.', '')
    
    words = line.split()
    formatted_line = []
    breakdown = []
    for word in words:
        syllable_count, syllables = count_syllables(word)
        breakdown.append(f"{word} ({syllable_count}) -> {syllables}")
        if syllable_count > 1:
            formatted_word = f"{word} {'+ ' * (syllable_count - 1)}".strip()
            formatted_line.append(formatted_word)
        else:
            formatted_line.append(word)
    return ' '.join(formatted_line), breakdown

def analyze_lyrics(lyrics):
    """
    Analyze lyrics for syllable breakdown and OpenUTAU formatting.
    Args:
        lyrics (str): Multi-line lyrics as input.
    Returns:
        tuple: Formatted lyrics, syllable breakdown, and total syllable count.
    """
    lines = lyrics.strip().split('\n')
    formatted_lines = []
    all_breakdowns = []
    total_syllables = 0

    for line in lines:
        formatted_line, breakdown = format_line_in_utau(line)
        formatted_lines.append(formatted_line)
        all_breakdowns.extend(breakdown)
        # Count syllables in the line
        for entry in breakdown:
            syllable_count = int(entry.split(' ')[1][1:-1])
            total_syllables += syllable_count

    return '\n'.join(formatted_lines), all_breakdowns, total_syllables

# # # German lyrics
# lyrics = """
# An deiner Seite fühl ich mich frei,
# Du bist die Sonne in meinem Mai.
# Deine Liebe gibt mir so viel Kraft,
# Mama, du bist, was das Leben schafft.
# Danke, liebe Mama, für jedes Jahr,
# Für jeden Moment, der so besonders war.
# Mit dir ist das Leben ein heller Tag,
# Deine Wärme bleibt, egal was kommt, stark.
# Im Garten, wo wir die Zeit oft teilen,
# Lass mich dir danken für all dein Heilen.
# Dein Lächeln gibt mir so viel Mut,
# Mama, bei dir ist alles gut.
# """

# lyrics="""
# In jeder Stunde, da bist du hier,
# Beste Freunde, das sind wir.
# Dein Lachen bringt die Sonne hervor,
# Mit dir fühl ich mich nie verloren.
# Danke, mein Freund, für die schöne Zeit,
# Du gibst mir Halt, bist immer bereit.
# Mit dir zu lachen, das macht mich froh,
# Egal wo wir sind, das bleibt immer so.
# Ob Regen oder Sonnenschein,
# Mit dir wird jeder Tag ein Fest sein.
# Du bist die Stärke, die mir oft fehlt,
# Unsere Freundschaft ist, was zählt
# """
# print(analyze_lyrics(lyrics))
# # Analyze lyrics
# formatted_lyrics, syllable_breakdown, total_syllables = analyze_lyrics(lyrics)

# # Print OpenUTAU-compatible formatted lyrics
# print("Formatted Lyrics (OpenUTAU Compatible):")
# print(formatted_lyrics)

# # Print syllable breakdown
# print("\nSyllable Breakdown (Word-by-Word):")
# for breakdown in syllable_breakdown:
#     print(breakdown)

# # Print total syllable count
# print(f"\nTotal Number of Syllables: {total_syllables}")
