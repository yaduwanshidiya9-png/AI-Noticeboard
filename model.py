import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Paths for saved model artifacts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'models')
CLASSIFIER_PATH = os.path.join(MODEL_DIR, 'classifier.pkl')

# Synthetic seed training data representing standard college notice contents
TRAINING_DATA = [
    # Exams
    ("End semester examination schedules and timetable are released.", "Exams"),
    ("Midterm assessment schedules and seating arrangement lists.", "Exams"),
    ("Retrieve your admit cards and hall tickets from the administrative office.", "Exams"),
    ("Strict instructions regarding exam rules, invigilation, and calculator policies.", "Exams"),
    ("Practical and viva-voce examination details for engineering branches.", "Exams"),
    ("Results, gradesheets, and marksheets will be published on the portal.", "Exams"),
    ("Make sure to clear library fines before the exam to get hall tickets.", "Exams"),
    
    # Placements
    ("Google campus recruitment drive for Software Engineer positions.", "Placements"),
    ("Submit resumes and register on the placement portal by tomorrow.", "Placements"),
    ("Mock interviews and group discussion training by the placement cell.", "Placements"),
    ("Placement interviews for final year mechanical engineering graduates.", "Placements"),
    ("Infosys off-campus pool drive details, eligibility criteria, and CTC package.", "Placements"),
    ("TCS is hiring developers. Register on the career hub link.", "Placements"),
    ("Pre-placement talk scheduled in the seminar hall for placement drives.", "Placements"),
    
    # Events
    ("Syntaxis Annual technical festival hackathon, coding, and robotics contest.", "Events"),
    ("Cultural society organizes music, dance, and theater events in the auditorium.", "Events"),
    ("Independence day celebrations and flag hoisting details on campus.", "Events"),
    ("Alumni meet and guest interactions scheduled for next Saturday.", "Events"),
    ("Inter-college sports meet, basketball, soccer, and chess tournament.", "Events"),
    ("Register for RoboWars and earn prizes worth lakhs.", "Events"),
    
    # Assignments
    ("Compiler design assignment on lexers and parsers submission guidelines.", "Assignments"),
    ("Submit your physics lab project reports and observation files on LMS.", "Assignments"),
    ("DBMS assignment 3 is uploaded. Submit before the due date.", "Assignments"),
    ("Microprocessor lab files and assignment submissions due this Friday.", "Assignments"),
    ("Prof A Sharma requests assignment submissions to be emailed directly.", "Assignments"),
    ("Late homework submissions will receive penalty marks.", "Assignments"),
    
    # Workshops
    ("Hands-on workshop on machine learning and deep learning with python.", "Workshops"),
    ("Two-day intensive seminar on block-chain and web3 development.", "Workshops"),
    ("Android application development training program for beginners.", "Workshops"),
    ("Web development workshop on React and Node js with certificates.", "Workshops"),
    ("Cloud computing AWS bootcamp hosted by certified specialists.", "Workshops"),
    ("Free webinar on research methodology and academic paper writing.", "Workshops"),
    
    # General
    ("Summer vacation starting dates and college reopening notifications.", "General"),
    ("Lost and found: Black leather folder containing certificates found in cafeteria.", "General"),
    ("College office rules for fee clearance, scholarship, and bus passes.", "General"),
    ("Anti-ragging committee guidelines and campus safety regulations.", "General"),
    ("Holiday announcement on the occasion of national festival.", "General"),
    ("Hostel gate timings and cafeteria menu updates for this month.", "General")
]

class NoticeClassifier:
    def __init__(self):
        self.model = None
        self._load_or_train()
        
    def _train(self):
        """Trains a new TfidfVectorizer + Naive Bayes pipeline and saves it."""
        print("Training a new Notice Classification ML model...")
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        texts = [x[0] for x in TRAINING_DATA]
        labels = [x[1] for x in TRAINING_DATA]
        
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english', min_df=1, ngram_range=(1, 2))),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        
        # Fit the model
        pipeline.fit(texts, labels)
        self.model = pipeline
        
        # Save to disk
        try:
            with open(CLASSIFIER_PATH, 'wb') as f:
                pickle.dump(pipeline, f)
            print(f"Model saved successfully to {CLASSIFIER_PATH}")
        except Exception as e:
            print(f"Error saving model: {e}")

    def _load_or_train(self):
        """Loads model from disk or triggers training if missing."""
        if os.path.exists(CLASSIFIER_PATH):
            try:
                with open(CLASSIFIER_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                print("Notice classification model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}. Retraining...")
                self._train()
        else:
            self._train()
            
    def predict(self, text):
        """Predicts the category of a given notice string."""
        if not text or not isinstance(text, str):
            return "General"
            
        if self.model is None:
            return "General"
            
        try:
            prediction = self.model.predict([text])[0]
            return prediction
        except Exception as e:
            print(f"Classification failed: {e}")
            return "General"

# Singleton instance
classifier_instance = None

def get_classifier():
    global classifier_instance
    if classifier_instance is None:
        classifier_instance = NoticeClassifier()
    return classifier_instance

def predict_category(text):
    """Utility wrapper for prediction."""
    return get_classifier().predict(text)

if __name__ == "__main__":
    # Test execution
    print("Testing classifier...")
    test_text = "There will be a campus recruitment drive by Microsoft for final year students."
    pred = predict_category(test_text)
    print(f"Text: '{test_text}' -> Predicted Category: {pred}")
