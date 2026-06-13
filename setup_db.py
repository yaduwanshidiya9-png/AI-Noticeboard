import os
from db import init_db, register_user, add_notice

def seed_database():
    print("Initializing SQLite Database...")
    init_db()
    
    print("Registering default users...")
    register_user("admin", "admin123", "admin", email="admin@institution.edu.in")
    register_user("student", "student123", "student", branch="Computer Science", year="3rd Year")
    
    print("Seeding sample college notices...")
    notices = [
        {
            "title": "End Semester Exams Schedule - May 2026",
            "content": "All students are hereby informed that the End Semester Examinations for all branches and semesters are scheduled to commence from June 10, 2026. Please ensure that all your academic fees and library dues are fully cleared before June 5, 2026, to receive your admit cards.",
            "summary": "End Semester Examinations start on June 10, 2026. All fees must be cleared by June 5 to collect admit cards.",
            "category": "Exams",
            "branch": "All",
            "year": "All",
            "priority": "High",
            "deadlines": "2026-06-05, 2026-06-10"
        },
        {
            "title": "Google Placement Drive for Class of 2026",
            "content": "The Training and Placement Cell is excited to announce a campus recruitment drive by Google for the role of Software Engineer. This drive is open to all final-year B.Tech students. Register by June 2, 2026.",
            "summary": "Google Software Engineer recruitment drive for final-year students. Register by June 2, 2026.",
            "category": "Placements",
            "branch": "Computer Science",
            "year": "4th Year",
            "priority": "High",
            "deadlines": "2026-06-02"
        }
    ]
    
    for notice in notices:
        add_notice(
            title=notice["title"],
            content=notice["content"],
            summary=notice["summary"],
            category=notice["category"],
            branch=notice["branch"],
            year=notice["year"],
            priority=notice["priority"],
            deadlines=notice["deadlines"]
        )
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
