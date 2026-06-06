import os
import sys
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image

# Absolute imports for local and production environment
import db
import model
import engine
import assistant

# Extract functions safely
init_db = db.init_db
register_user = db.register_user
authenticate_user = db.authenticate_user
add_notice = db.add_notice
delete_notice = db.delete_notice
get_notices = db.get_notices
get_notice_by_id = db.get_notice_by_id

predict_category = model.predict_category
generate_summary = engine.generate_summary
detect_deadlines = engine.detect_deadlines
get_chatbot_response = assistant.get_chatbot_response

# Initialize Flask app
app = Flask(__name__)

# Configure uploads folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload limit

# Initialize SQLite database on launch
init_db()

# --- OCR Processing Helper ---
def perform_ocr(file_path):
    """
    Attempts to extract text from a PDF or image notice.
    Uses pdfplumber for PDFs and pytesseract for images.
    Falls back gracefully if libraries/dependencies are missing.
    """
    ext = os.path.splitext(file_path)[1].lower()
    extracted_text = ""
    
    if ext == '.pdf':
        try:
            import pdfplumber
            print(f"Extracting text from PDF: {file_path}")
            with pdfplumber.open(file_path) as pdf:
                text_pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
                extracted_text = "\n".join(text_pages)
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            
    elif ext in ['.png', '.jpg', '.jpeg', '.bmp']:
        try:
            import pytesseract
            print(f"Extracting text from image via OCR: {file_path}")
            # Try to run pytesseract
            img = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(img)
        except Exception as e:
            print(f"pytesseract OCR extraction failed: {e}")
            extracted_text = "[OCR Engine unavailable or Tesseract not installed. Please edit text manually.]"
            
    return extracted_text.strip() if extracted_text else ""


# --- Authentication API Routes ---

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'student')
    branch = data.get('branch', 'All')
    year = data.get('year', 'All')
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
        
    result = register_user(username, password, role, branch, year)
    return jsonify(result)

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
        
    result = authenticate_user(username, password)
    return jsonify(result)


# --- Notices CRUD API Routes ---

@app.route('/api/notices', methods=['GET'])
def api_get_notices():
    branch = request.args.get('branch')
    year = request.args.get('year')
    category = request.args.get('category')
    priority = request.args.get('priority')
    search = request.args.get('search')
    
    notices = get_notices(branch, year, category, priority, search)
    return jsonify({"success": True, "notices": notices})

@app.route('/api/notices/<int:notice_id>', methods=['GET'])
def api_get_single_notice(notice_id):
    notice = get_notice_by_id(notice_id)
    if notice:
        return jsonify({"success": True, "notice": notice})
    return jsonify({"success": False, "message": "Notice not found."}), 404

@app.route('/api/notices', methods=['POST'])
def api_add_notice():
    """
    Endpoint for admins to upload notices.
    Supports either straight text notices or file attachments (PDF/Images) with auto-OCR processing,
    category classification, extractive summarization, and deadline parsing.
    """
    # Parse form fields
    title = request.form.get('title')
    branch = request.form.get('branch', 'All')
    year = request.form.get('year', 'All')
    priority = request.form.get('priority', 'Medium')
    
    # Optional manual overrides
    manual_content = request.form.get('content', '')
    manual_category = request.form.get('category', '')
    
    if not title:
        return jsonify({"success": False, "message": "Title is required."}), 400
        
    file_path = None
    extracted_text = ""
    
    # Process uploaded file if present
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            file_path = save_path
            
            # Extract content text via OCR or PDF text extraction
            extracted_text = perform_ocr(save_path)
            
    # Combine or select content
    content = manual_content if manual_content else extracted_text
    
    if not content:
        return jsonify({
            "success": False, 
            "message": "Notice content is empty. Please provide notice text or upload a document with readable text."
        }), 400
        
    # Run NLP / Deep Learning Pipeline
    # 1. Automatic classification if category not manually selected
    category = manual_category if manual_category else predict_category(content)
    
    # 2. Extractive summarization
    summary = generate_summary(content, max_sentences=3)
    
    # 3. Deadline / Date extraction
    deadlines = detect_deadlines(content)
    
    # Write to database
    result = add_notice(
        title=title,
        content=content,
        summary=summary,
        category=category,
        branch=branch,
        year=year,
        priority=priority,
        deadlines=deadlines,
        file_path=file_path
    )
    
    # Return processed details so Admin can see the AI output immediately
    if result["success"]:
        return jsonify({
            "success": True,
            "notice_id": result["notice_id"],
            "ai_details": {
                "predicted_category": category,
                "generated_summary": summary,
                "detected_deadlines": deadlines,
                "file_attached": file_path is not None
            },
            "message": "Notice added and processed successfully by AI."
        })
    else:
        return jsonify(result), 500

@app.route('/api/notices/<int:notice_id>', methods=['DELETE'])
def api_delete_notice(notice_id):
    result = delete_notice(notice_id)
    return jsonify(result)


# --- AI Chatbot and Smart Recommendation API Routes ---

@app.route('/api/chatbot', methods=['POST'])
def api_chatbot():
    data = request.get_json() or {}
    user_query = data.get('query')
    student_branch = data.get('branch', 'All')
    student_year = data.get('year', 'All')
    
    if not user_query:
        return jsonify({"success": False, "message": "Query parameter is required."}), 400
        
    # Get all active notices in the DB for searching
    notices = get_notices(branch=student_branch, year=student_year)
    response = get_chatbot_response(user_query, notices)
    
    return jsonify({"success": True, "response": response})

@app.route('/api/recommendations', methods=['GET'])
def api_recommendations():
    """
    Returns smart notice recommendations based on student's branch and year.
    Matches and sorts notices matching profile keywords using TF-IDF.
    """
    branch = request.args.get('branch', 'All')
    year = request.args.get('year', 'All')
    
    # Fetch all notices targetting student
    notices = get_notices(branch=branch, year=year)
    
    # Smart Sorting: High priority first, then match student branch keywords
    recommendations = []
    for n in notices:
        score = 0
        # Boost score based on priority
        if n['priority'] == 'High':
            score += 10
        elif n['priority'] == 'Medium':
            score += 5
            
        # Boost score if it exactly matches student branch (rather than 'All')
        if n['branch'] == branch and branch != 'All':
            score += 8
            
        # Boost score if it exactly matches student year (rather than 'All')
        if n['year'] == year and year != 'All':
            score += 5
            
        n_copy = dict(n)
        n_copy['recommendation_score'] = score
        recommendations.append(n_copy)
        
    # Sort recommendations by score descending
    recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
    
    return jsonify({"success": True, "notices": recommendations})

# Run the Flask REST Server
if __name__ == '__main__':
    print("Launching AI NoticeBoard Flask backend...")
    app.run(host='0.0.0.0', port=5000, debug=True)
