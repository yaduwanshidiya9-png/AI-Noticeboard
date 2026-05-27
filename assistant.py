import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def clean_query(query):
    """Cleans the input user query."""
    return re.sub(r'[^\w\s]', '', query.lower().strip())

def get_chatbot_response(user_query, notices):
    """
    Analyzes the student query and searches the list of database notices
    to return a highly relevant, context-aware markdown response.
    
    Uses TF-IDF Vectorization and Cosine Similarity to find semantic matches,
    supported by category-specific intent matching for high precision.
    """
    if not notices:
        return "There are no notices posted on the board yet! Once an administrator uploads notices, I will be able to answer your questions."
        
    cleaned_query = clean_query(user_query)
    
    # 1. Check for quick intent matching to deliver a high-quality user experience
    is_exam_query = any(word in cleaned_query for word in ["exam", "test", "quiz", "datesheet", "schedule", "admit card", "hall ticket"])
    is_placement_query = any(word in cleaned_query for word in ["placement", "job", "recruit", "internship", "hiring", "company", "interview", "ctc"])
    is_event_query = any(word in cleaned_query for word in ["event", "fest", "hackathon", "annual", "cultural", "sports", "syntaxis"])
    is_workshop_query = any(word in cleaned_query for word in ["workshop", "seminar", "bootcamp", "training", "webinar"])
    is_assignment_query = any(word in cleaned_query for word in ["assignment", "submission", "due date", "homework", "lab report"])
    is_deadline_query = any(word in cleaned_query for word in ["deadline", "due", "last date", "urgent", "before"])
    
    # Filter notices based on intent keyword triggers first
    matched_notices = []
    
    if is_exam_query:
        matched_notices = [n for n in notices if n['category'] == 'Exams']
    elif is_placement_query:
        matched_notices = [n for n in notices if n['category'] == 'Placements']
    elif is_event_query:
        matched_notices = [n for n in notices if n['category'] == 'Events']
    elif is_workshop_query:
        matched_notices = [n for n in notices if n['category'] == 'Workshops']
    elif is_assignment_query:
        matched_notices = [n for n in notices if n['category'] == 'Assignments']
    elif is_deadline_query:
        # Get any notices that have active deadlines detected
        matched_notices = [n for n in notices if n['deadlines']]

    # 2. If an intent is matched and we have notices, construct a direct response
    if matched_notices:
        response = f"📚 **Here are the relevant updates matching your query:**\n\n"
        for idx, n in enumerate(matched_notices[:3], 1):
            deadline_str = f" ⏳ **Deadline:** `{n['deadlines']}`" if n['deadlines'] else ""
            response += f"**{idx}. {n['title']}** ({n['category']})\n"
            response += f"> 📝 *Summary:* {n['summary']}\n"
            if deadline_str:
                response += f"> {deadline_str}\n"
            response += "\n"
        return response
        
    # 3. TF-IDF + Cosine Similarity fallback for semantic lookup
    try:
        # Build document corpus from notices
        corpus = []
        for n in notices:
            # Combine title and content to represent the notice
            document = f"{n['title']} {n['content']} {n['category']}"
            corpus.append(document)
            
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(corpus)
        query_vector = vectorizer.transform([user_query])
        
        # Calculate cosine similarity of query with all notices
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        max_idx = similarities.argmax()
        max_similarity = similarities[max_idx]
        
        if max_similarity > 0.15:
            matched = notices[max_idx]
            deadline_tag = f"\n\n⏳ **Important Deadline(s):** `{matched['deadlines']}`" if matched['deadlines'] else ""
            return (
                f"💡 **I found a notice that seems relevant:**\n\n"
                f"### **{matched['title']}**\n"
                f"**Category:** `{matched['category']}` | **Priority:** `{matched['priority']}`\n\n"
                f"📝 **Summary:**\n{matched['summary']}\n\n"
                f"📖 **Full Content:**\n{matched['content']}{deadline_tag}"
            )
    except Exception as e:
        print(f"TF-IDF Chatbot search encountered error: {e}")
        
    # 4. Catch-all fallback default responses
    return (
        "🤖 **Hello!** I am the AI NoticeBoard Assistant. I can help you find notices regarding:\n"
        "- **Exams** (e.g. 'When are the exams starting?')\n"
        "- **Placements** (e.g. 'Any placement drives or Google jobs?')\n"
        "- **Events** (e.g. 'Tell me about the annual tech fest')\n"
        "- **Workshops** (e.g. 'Are there any Python workshops?')\n"
        "- **Assignments** (e.g. 'What assignments are due?')\n\n"
        "Try rephrasing your question or check the Notice Board dashboard!"
    )
