import pyphen

# Initialize Pyphen for Romanian syllabification
syllable_splitter = pyphen.Pyphen(lang='el_GR')

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


def process_ballad_lyrics(lyrics):
    """
    Process Greek lyrics by merging the last line with the preceding one,
    keeping everything after '...' as a separate line.
    If '...' is not found, the last line should contain at least 6 words.

    Parameters:
    - lyrics: String containing the lyrics.

    Returns:
    - A list of formatted lyric lines.
    """
    import re
    
    # Split lyrics into lines and remove empty lines
    lines = [line.strip() for line in lyrics.strip().split("\n") if line.strip()]

    # Ensure lyrics have at least two lines
    if len(lines) < 2:
        raise ValueError("Lyrics must have at least two lines to process.")

    # Find the last line and check for "..."
    last_line = lines[-1]
    match = re.search(r"(.*?)\.\.\.(.*)", last_line)

    if match:
        # Extract parts before and after '...'
        before_ellipsis = match.group(1).strip()
        after_ellipsis = match.group(2).strip()

        # Merge the part before "..." with the previous line
        lines[-2] += " " + before_ellipsis
        lines[-1] = after_ellipsis  # Keep everything after "..." as a new line
    else:
        # If '...' not found, ensure the last line has at least 6 words
        words = last_line.split()
        if len(words) < 6:
            if len(lines) > 1:
                # Move words from the second last line to the last to reach 6 words
                previous_line_words = lines[-2].split()
                while len(words) < 6 and previous_line_words:
                    words.insert(0, previous_line_words.pop())

                # Update the last two lines
                lines[-2] = " ".join(previous_line_words)
                lines[-1] = " ".join(words)
                
            if len(words) < 6:
                raise ValueError("Cannot ensure the last line has at least 6 words.")

    return [line for line in lines if line.strip()]

lyrics = """
Χριστίνα με φωτογραφίζεις,
συνέχεια κι ανελλιπώς.
Ακούραστα τραβάς τις λήψεις,
ενώ ποζάρω διαρκώς.
Τραβάς τρακόσιες φωτογραφίες,
χωρίς να λες «πια δεν μπορώ».
Βρίσκεις γωνίες που μου ταιριάζουν
και ποιο προφίλ μου είναι καλό.
Κι αν χίλια κλικ σου ζητήσω,
πάνω σου εγώ θα βασίσω
τις λήψεις που θ’ ανεβάσω,
και έτσι δεν θα κάτσω να σκάσω .
Κι αν φωτογένεια δεν έχω,
την κολλητή μου πάντα προσέχω.
Γιατί ποτέ σου κάτω δεν το βάζεις
Κι έτσι καλύτερες λήψεις βγάζεις.
"""

lyrics = """
Το τηλεκοντρόλ βουτάει 
Στου καναπέ το κενό 
Κι η Κλειώ τ’ αναζητάει, 
Κι όσο ‘γώ παντού το ψάχνω, ‘κείνη βρίσκει που ‘χει πάει. 
Και φωνάζω στο σαλόνι, Κλειώ είσαι μια θεά
Γιατί επιτέλους βλέπω τις σειρές μου εγώ ξανά. 
Και όταν πάω να το χάσω, το εντοπίζεις μαγικά, 
Σ’ αγαπώ, που πάντα βρίσκεις το τηλεκοντρόλ ξανά
"""

lyrics = """
Κάθε στιγμή,
μαμά εσύ
στο τηλέφωνό με παίρνεις
για καθετί.
Κι αν με παίρνεις όλη μέρα
και δεν απαντά,
ξέρεις πως σε αγαπάω
μα έχω και δουλειά.
Κι αν εγώ δεν το σηκώσω
πάλι θα στο πω
Στην καρδιά μου σ’ εχω όμως
δεν έχω ρεπό.
"""
lyrics = """
Είσαι εκεί,
Καρδιά μισή,
Κάψαμε όσα αξίζουν
σε μια στιγμή
Κι αν βρεθούμε μην πιστέψεις όσα θα σου πω
Πώς τις νύχτες δεν δακρύζω
Πώς δεν σ αγαπώ
Κι αν την πλάτη σου γυρίσω
κάπως βιαστικά
Είναι η βροχή στα μάτια
Που δεν σταματά
"""
lyrics = """
Η σιωπή σου με ξυπνάει,
Μες της νύχτας το κενό
Και ο χρόνος που κυλάει,
Πιο μακριά σε παρασέρνει, την αγάπη μας σκορπάει
Και φωνάζω στις πλατείες, το όνομα σου μα κενό,
Χάνομαι μέσα στις μνήμες που ακόμη αγαπώ,
Ένα χάδι, ένα φιλί σου, ένα βλέμμα είν' αρκετό,
Για να αφήσω ότι έχω και να έρθω να σε βρω.
"""
lyrics="""
Ξυπνητήρι μου χτυπάει,
με τον σκύλο για να βγω,
Μα εσύ 'σαι πάντα εκεί,
Το λουρί του να του δώσεις, και να φύγετε μαζί.
Και φωνάζω απ' το κρεβάτι, Γιάννη, είσαι φοβερός
Με τον σκύλο κάθε μέρα, περπατάς αγέρωχος.
Ένα βλέμμα, ένα βήμα, κι όλα μοιάζουν ξαφνικά,
Γιατί εσύ τον βγάζεις βόλτα κι εγώ μένω στα ζεστά
"""

lyrics = """
Είσαι εκεί,
Καρδιά μισή,
Κάψαμε όσα αξίζουν
σε μια στιγμή
Κι αν βρεθούμε μην πιστέψεις όσα θα σου πω
Πώς τις νύχτες δεν δακρύζω
Πώς δεν σ αγαπώ
Κι αν την πλάτη σου γυρίσω
κάπως βιαστικά
Είναι η βροχή στα μάτια
Που δεν σταματά
"""

lyrics = """
Είσαι εκεί,
Καρδιά μισή,
Κάψαμε όσα αξίζουν
σε μια στιγμή
Κι αν βρεθούμε μην πιστέψεις όσα θα σου πω
Πώς τις νύχτες δεν δακρύζω
Πώς δεν σ αγαπώ
Κι αν την πλάτη σου γυρίσω
κάπως βιαστικά
Είναι η βροχή στα μάτια
Που δεν σταματά
"""

lyrics = """
Είσαι εκεί,
Καρδιά μισή,
Κάψαμε όσα αξίζουν
σε μια στιγμή
Κι αν βρεθούμε μην πιστέψεις όσα θα σου πω
Πώς τις νύχτες δεν δακρύζω
Πώς δεν σ αγαπώ
Κι αν την πλάτη σου γυρίσω
κάπως βιαστικά
Είναι η βροχή στα μάτια
Που δεν σταματά
"""

lyrics = """
Εσύ το gif, εγώ το caption,
Κι οι δυο μαζί, ένα trend τρελό
Τα memes σου όταν με βρουν σε θλίψη,
Το κέφι μου φτάνει εδώ.
Εσύ το Trend, εγώ η τάση
Κι οι δυο μαζί, μαγεία online.
Κι όταν μου λες «σου στέλνω κάτι»,
Θα γελάω σαν παιδί.
Και αν το feed ησυχάσει,
Η έμπνευσή δε θα πάψει,
Μάρκο, εγώ σ’ αγαπάω,
κι ας μη το λέω, αν με ρωτάνε.
Κι αν η μέρα έχει πλάκα,
Αρκεί τοτέ μια ατάκα
Μάρκο, λατρεία, vibe τρελό,
Είναι τα memes σου flow σωστό
"""
lyrics = """
Η σιωπή σου με ξυπνάει,
Μες της νύχτας το κενό
Και ο χρόνος που κυλάει,
Πιο μακριά σε παρασέρνει, την αγάπη μας σκορπάει
Και φωνάζω στις πλατείες, το όνομα σου μα κενό,
Χάνομαι μέσα στις μνήμες που ακόμη αγαπώ,
Ένα χάδι, ένα φιλί σου, ένα βλέμμα είν' αρκετό, 
Για να αφήσω ότι έχω...και να έρθω να σε βρω
"""
# print(analyze_lyrics(lyrics))


"""
Η σιωπή + σου με ξυπνάει +
Μες της νύχτας + το κενό +
Και ο χρόνος που κυλάει +
Πιο μακριά + σε παρασέρνει + + + την αγάπη μας σκορπάει +
Και φωνάζω + στις πλατείες + + το όνομα + σου μα κενό +
Χάνομαι + μέσα στις μνήμες + που ακόμη αγαπώ +
Ένα χάδι ένα φιλί + σου ένα βλέμμα + είν' + αρκετό + +
Για να αφήσω + ότι έχω και να έρθω + να σε βρω
"""


"""
Είσαι + εκεί
Καρδιά + μισή +
Κάψαμε + όσα αξίζουν +
σε μια στιγμή +
Κι αν βρεθούμε + + μην πιστέψεις + όσα θα σου πω
Πώς τις νύχτες + δεν δακρύζω + +
Πώς δεν σ αγαπώ +
Κι αν την πλάτη σου γυρίσω + +
κάπως βιαστικά + +
Είναι + η βροχή + στα μάτια
Που δεν σταματά + +
"""