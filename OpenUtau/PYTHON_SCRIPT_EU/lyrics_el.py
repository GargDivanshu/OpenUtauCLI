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