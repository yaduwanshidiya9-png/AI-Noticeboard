
A smart, AI-powered noticeboard that helps schools and colleges share, prioritize, and personalize notices for students and admins — built with **Flask**, **Streamlit**, and **Machine Learning**.

---

## ✨ What is this?

The **AI Noticeboard System** replaces boring paper noticeboards with an intelligent dashboard that:

- 📌 **Posts & organizes notices** in one clean place
- 🧠 **Uses ML models** to categorize and prioritize notices automatically
- 👥 **Personalizes feeds** for students vs. admins
- ⚡ **Updates in real time** via a Flask REST API
- 📊 **Visualizes everything** through a beautiful Streamlit dashboard

---

## 🏗️ Tech Stack

| Layer | Technology |
|------|-----------|
| 🎨 Frontend | Streamlit |
| ⚙️ Backend | Flask (REST API) |
| 🗄️ Database | SQLite |
| 🤖 AI / ML | Pre-trained models (seeded on setup) |

---

## 🚀 Getting Started

Follow these **3 simple steps** to get the project running locally.

### 1️⃣ Setup the Database & Pre-train ML Models

Initializes the SQLite database and seeds it with mock notices + trained models.

```bash
python setup_db.py
```

### 2️⃣ Launch the Flask Backend API

Starts the REST API server on **port 5000**.

```bash
python server.py
```

> 💡 Keep this terminal running.

### 3️⃣ Start the Streamlit Dashboard

Open a **new terminal** and launch the frontend:

```bash
python -m streamlit run dashboard.py
```

🎉 Your dashboard will open automatically in the browser!

---

## 🔐 Default Login Credentials

Use these accounts to test the system out of the box:

### 👑 Admin
```
Username: admin
Password: admin123
```

### 🎒 Student
```
Username: student
Password: student123
```

---

## 🗺️ Project Flow

```
   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
   │  setup_db.py │ ───▶ │  server.py   │ ───▶ │ dashboard.py │
   │  DB + ML init│      │  Flask API   │      │  Streamlit UI│
   └──────────────┘      └──────────────┘      └──────────────┘
```

---

## 🧰 Troubleshooting

- **Port 5000 already in use?** → Stop other apps or change the port in `server.py`.
- **Streamlit not found?** → Run `pip install streamlit flask scikit-learn`.
- **Database errors?** → Delete the existing `.db` file and re-run `python setup_db.py`.

---

## 💖 Enjoy building smarter campuses!
