import openai
import os
import re
import pyphen

# Choose method: "PYPHEN" or "OPENAI"
SYLLABLE_METHOD = "OPENAI"  # Change to "OPENAI" to use GPT

# Initialize Pyphen for Greek syllabification
syllable_splitter = pyphen.Pyphen(lang='el_GR')

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
        " Όταν το γράμμα «ι» (γιώτα) βρίσκεται μετά από ένα σύμφωνο και πριν από ένα άλλο φωνήεν, αλλά χωρίς τόνο στο «ι», "
        "η τριάδα διαβάζεται σαν μια συλλαβή. Για παράδειγμα το \"μια\" και το \"τιά\" είναι μία συλλαβή, ενώ το \"μία\" είναι δύο συλλαβές. "
        "Το «κι» ενώνεται με το φωνήεν της επόμενης λέξης και δημιουργεί μία συλλαβή. Για παράδειγμα, το «κι αν» ή το «κι αυτό» έχουν μία συλλαβή, "
        "παρόλο που περιέχουν δύο λέξεις. Παράδειγμα, αν η φράση είναι κι ο χρόνος, ο συλλαβισμός είναι κιο(1) χρόνος (2). "
        "Όταν χρησιμοποιούμε απόστροφο για να δείξουμε ότι ένα φωνήεν παραλείπεται, οι λέξεις που ενώνουμε συγχωνεύονται σε μία συλλαβή. "
        "Για παράδειγμα στο «γι’ αυτό» το «ι» ενώνεται με το «α» και προφέρονται μαζί, άρα η φράση αποτελείται από 2 συλλαβές. "
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

def format_line_in_utau(lyrics):
    """
    Format lyrics into OpenUTAU format based on syllable counts.
    
    Parameters:
    - lyrics: Lyrics string.

    Returns:
    - Formatted lyrics string.
    """
    if SYLLABLE_METHOD == "OPENAI":
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

def analyze_lyrics(lyrics):
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
        formatted_line = format_line_in_utau(line)
        formatted_lines.append(formatted_line)

    return '\n'.join(formatted_lines)

def process_ballad_lyrics(lyrics):
    """
    Process Greek lyrics by merging the last line with the preceding one,
    keeping everything after '...' as a separate line.

    Parameters:
    - lyrics: String containing the lyrics.

    Returns:
    - A tuple containing:
        1. A formatted lyrics string with proper line breaks.
        2. A list of formatted lyric lines.
    """
    import re

    # Print initial lyrics
    print("Initial lyrics:\n")
    print(lyrics)

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

    # Create formatted lyrics string
    formatted_lyrics_str = "\n".join(lines)

    # Print processed lyrics
    print("\nProcessed lyrics:\n")
    print(formatted_lyrics_str)

    return formatted_lyrics_str, lines


# Example usage
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

print("\nFinal OpenUTAU Formatted Lyrics:\n")
print(analyze_lyrics(lyrics))



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

lyrics = """
Εσύ τα αστέρια, εγώ η νύχτα,
Και οι δυο μαζί, ο ουρανός.
Τα μάτια σου, όταν τα βρήκα,
Ο κόσμος γέμισε με φως.
Εσύ το βλέμμα, εγώ η σκέψη,
Και οι δυο μαζί, η μουσική.
Τα χέρια σου όταν μ ‘αγγίξαν,
Στο σύμπαν δώσαμε πνοή.
Και αν ο χρόνος παγώσει,
Η αγάπη μας θα γλυτώσει,
Μέσα στο άπειρο πάμε,
Δε σταματάμε, δε στα-μα-τά-με.
Και αν (όταν) όλα σκορπίσουν,
Τα αστέρια μας ξανά θα φωτίσουν,
Μέσα στο χάος θα βρω τη φωνή σου,
Θα’μαι μαζί σου, για πάντα μαζί σου.
"""

"""
Εσύ τα αστέρια εγώ η νύχτα +
Και οι δυο μαζί + ο ουρανός + +
Τα μάτια σου όταν τα βρήκα +
Ο κόσμος γέμισε + με φως
Εσύ το βλέμμα + εγώ η σκέψη
Και οι δυο μαζί + η μουσική + +
Τα χέρια σου όταν μ ‘αγγίξαν + +
Στο σύμπαν + δώσαμε + πνοή
Και αν ο χρόνος παγώσει +
Η αγάπη μας θα γλυτώσει +
Μέσα στο άπειρο + πάμε
Δε σταματάμε + + δε στα-μα-τά-με + + + + +
Και αν (όταν) + όλα σκορπίσουν + +
Τα αστέρια μας ξανά + θα φωτίσουν + +
Μέσα στο χάος θα βρω τη φωνή + σου
Θα’μαι + μαζί + σου για πάντα μαζί + σου
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