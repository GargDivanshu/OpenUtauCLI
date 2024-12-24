import pyphen

# Initialize Pyphen for Romanian syllabification
syllable_splitter = pyphen.Pyphen(lang='sk_SK')

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