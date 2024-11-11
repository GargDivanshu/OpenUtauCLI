import re

def process_lyrics(lyrics_text):
    """Process lyrics text by replacing syllable counts with '+' signs and removing unwanted characters."""
    # Replace syllable counts (e.g., (2)) with '+' signs
    lyrics_text = re.sub(r'\((\d)\)', lambda x: ' +' * (int(x.group(1)) - 1), lyrics_text)
    
    # Remove all punctuation except '+' and whitespace
    lyrics_text = re.sub(r'[^\w\s\+]', '', lyrics_text)
    
    # Remove any commas
    lyrics_text = lyrics_text.replace(',', '')
    
    return lyrics_text


def utau_lyrics_main(lyrics_text):
    """Main function to process lyrics and print syllable counts for sample words."""
    
    # Process the lyrics text
    processed_lyrics = process_lyrics(lyrics_text)
    
    print("Processed Lyrics:\n", processed_lyrics)
    return processed_lyrics
    
    # Example usage of syllable count function
    # sample_words = ["supportive", "fun", "day"]
    # for word in sample_words:
    #     print(f"Syllable count for '{word}': {syllable_count(word)}")

# Run the main function if the script is executed directly
