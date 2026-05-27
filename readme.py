============================================================
🎓             AI NOTICEBOARD SYSTEM SETUP GUIDE            🎓
============================================================

💻 HOW TO RUN THE PROJECT:
------------------------------------------------------------

1️⃣  [STEP 1] Setup the Database & Pre-train ML Models:
   Run this command to initialize SQLite database and seed mock notices:
      python setup_db.py

2️⃣  [STEP 2] Launch the Flask Backend API Server:
   Open a terminal and start the backend REST API on Port 5000:
      python server.py

3️⃣  [STEP 3] Start the Streamlit Frontend Client:
   Open a second terminal window and launch the visual dashboard:
      python -m streamlit run dashboard.py

------------------------------------------------------------
 DEFAULT USER LOGIN CREDENTIALS:
------------------------------------------------------------
👤 Admin Account:
   Username: admin
   Password: admin123

👤 Student Account:
   Username: student
   Password: student123
============================================================
