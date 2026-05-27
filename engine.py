import re
import string

# Hardcoded list of English stopwords for fallback in case nltk corpora are not available
ENGLISH_STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", 
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 
    'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 
    'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 
    'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 
    'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 
    'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 
    'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 
    'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', 
    "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 
    'wouldn', "wouldn't", 'hereby', 'thereby', 'herein', 'therein', 'shall', 'please'
}

def clean_text(text):
    """Removes special characters and lowercases the text."""
    text = re.sub(r'\[[0-9]*\]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def sentence_tokenize(text):
    """Tokenizes text into sentences using regex."""
    # Split on sentence terminals followed by spaces and capital letters
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    return [s.strip() for s in sentences if s.strip()]

def word_tokenize(text):
    """Tokenizes text into words."""
    # Remove punctuation and split by whitespace
    clean = text.translate(str.maketrans('', '', string.punctuation))
    return clean.lower().split()

def generate_summary(text, max_sentences=3):
    """
    Generates a concise summary from input text using an extractive TF-based frequency algorithm.
    Falls back gracefully if the input text is too short.
    """
    if not text or not isinstance(text, str):
        return ""
        
    cleaned_text = clean_text(text)
    sentences = sentence_tokenize(text)
    
    # If the text is very short (3 or fewer sentences), return the original text directly.
    if len(sentences) <= max_sentences:
        return text.strip()
        
    words = word_tokenize(cleaned_text)
    
    # Calculate word frequency
    word_frequencies = {}
    for word in words:
        if word not in ENGLISH_STOPWORDS:
            word_frequencies[word] = word_frequencies.get(word, 0) + 1
            
    # Normalize frequencies
    if not word_frequencies:
        # Fallback to first few sentences if no keywords are parsed
        return " ".join(sentences[:max_sentences])
        
    max_frequency = max(word_frequencies.values())
    for word in word_frequencies:
        word_frequencies[word] = word_frequencies[word] / max_frequency
        
    # Score sentences based on word frequencies
    sentence_scores = {}
    for sent in sentences:
        sent_words = word_tokenize(sent)
        for word in sent_words:
            if word in word_frequencies:
                sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word]
                
    # Sort and pick top sentences
    if not sentence_scores:
        return " ".join(sentences[:max_sentences])
        
    # Get the top scoring sentences
    sorted_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
    top_sentences = sorted_sentences[:max_sentences]
    
    # Re-order the top sentences to match the original text sequence
    ordered_sentences = []
    for sent in sentences:
        if sent in dict(top_sentences):
            ordered_sentences.append(sent)
            
    return " ".join(ordered_sentences)

def detect_deadlines(text):
    """
    Automatically detects dates and deadlines in a notice text using regex patterns.
    Returns a comma-separated string of unique formatted dates.
    """
    if not text or not isinstance(text, str):
        return ""
        
    # Regular expressions for common date formats:
    # 1. DD/MM/YYYY or DD-MM-YYYY (e.g. 15/06/2026, 12-10-2026)
    # 2. Month DD, YYYY (e.g. June 15, 2026, May 27th, 2026)
    # 3. YYYY-MM-DD
    patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # 15/06/2026 or 15-06-26
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}\b', # June 15th, 2026
        r'\b\d{4}-\d{2}-\d{2}\b', # 2026-06-15
        r'\b(?:before|on|by)\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}\b' # "by June 12"
    ]
    
    dates_found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            # Standardize spacing and strip prefix words like "by", "before"
            clean_m = re.sub(r'^(by|on|before)\s+', '', m, flags=re.IGNORECASE)
            dates_found.append(clean_m.strip())
            
    # Remove duplicates preserving order
    unique_dates = []
    for d in dates_found:
        if d not in unique_dates:
            unique_dates.append(d)
            
    return ", ".join(unique_dates)

if __name__ == "__main__":
    # Test execution
    test_notice = (
        "This is to notify all CSE B.Tech students that the Compiler Design lab files must be submitted "
        "before June 8, 2026. Submissions must be uploaded directly to the university LMS portal. "
        "Each assignment must follow the proper formatting with a cover page. "
        "The project consists of creating a lexical analyzer using lex tools. "
        "Late submissions will result in a heavy penalty of 2 marks per day. "
        "Ensure all details are correct. Contact Prof. Sharma in case of queries by June 5, 2026."
    )
    
    print("Test Summary:")
    print(generate_summary(test_notice, max_sentences=2))
    print("\nTest Deadlines:")
    print(detect_deadlines(test_notice))
