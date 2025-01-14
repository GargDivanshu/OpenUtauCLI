import pyphen

# Initialize Pyphen for German syllabification
syllable_splitter = pyphen.Pyphen(lang='es_ES')

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
# Mariana, gracias por llegar
# a mi vida y siempre estar
# en las buenas y en las malas,
# tu amistad no se va.
# Con tu alegría,
# me contagias cada día.
# Eres luz en mi camino,
# un tesoro genuino.
# Gracias, Mariana, en verdad
# por tu apoyo y tu amistad.
# Eres única y especial,
# un regalo sin igual.
# Te quiero agradecer,
# por todo lo que haces crecer.
# Tu amistad es mi bendición;
# mi refugio, mi inspiración.
# """
# lyrics="""
# Hoy es tu día, Mateo,
# que cumplas muchos más,
# que la vida te regale,
# felicidad y paz.
# Que en este año nuevo,
# se cumplan tus deseos,
# y que siempre te rodees,
# solo de amigos buenos.
# Feliz cumpleaños, Mateo,
# que te la pases genial,
# que sea un día muy especial,
# lleno de alegría sin igual.
# Que el futuro sea brillante,
# y tus sueños sean realidad,
# que sigas celebrando siempre,
# con amor y felicidad.
# """
# lyrics = """
# Sofía, amiga fiel,
# siempre estás cuando te llamo,
# un consejo, una ayuda,
# tu amistad es mi aliento.
# En todo momento,
# sé que cuento contigo,
# tu apoyo es mi regalo,
# que ilumina mi camino.
# Gracias, Sofía, de corazón,
# por tu amistad única,
# eres un tesoro,
# siempre te cuidaré.
# Tu sonrisa, tu bondad,
# tu energía especial,
# Sofía, gracias por ser tú,
# mi amiga más leal.
# """
lyrics = """
Fernando, mi querido amigo, 
eres team calor, lo admito, 
hablas hasta por los codos, 
a veces un poco extremo. 
No te gusta la basura, 
odias esa tarea, 
pero siempre algún dato, 
interesante nos entregas.
Bailas con tanto estilo, 
es lo que más aprecio, 
amas a todos los perros, 
tu corazón tan sincero. 
Fernando, con todo mi ser, 
te digo eres genial, 
con cariño, Bubulubu, 
nunca dejes de brillar.
"""
lyrics = """
Hoy celebro tu cumpleaños,
en Puebla habrá festejo.
Guillermo, eres especial,
que se te cumplan tus sueños.
TE DE SE O
Que tu risa no se acabe,
cada meta que la alcances,
y que la vida te abrace.
Feliz día para ti,
con amor y porvenir.
Eres luz en cada paso,
tu alegría siempre es abrazo.
Tus sueños se cumplirán,
llenos de felicidad.
Hoy la vida es para ti,
siempre brilla y sé feliz.
"""
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
