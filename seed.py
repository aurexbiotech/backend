"""Seed script to populate or update test accounts for all HMS roles.

Usage:
    python seed.py
"""

from auth import hash_password
from database import SessionLocal
from models import User

DEMO_PASSWORD = "Password123!"

SEED_ACCOUNTS = [
    {
        "full_name": "Elena Vance (Patient)",
        "email": "patient@aurex.com",
        "phone_number": "555-0101",
        "role": "patient",
    },
    {
        "full_name": "Dr. Sarah Chen (Doctor)",
        "email": "doctor@aurex.com",
        "phone_number": "555-0102",
        "role": "doctor",
    },
    {
        "full_name": "Nurse James Wilson",
        "email": "nurse@aurex.com",
        "phone_number": "555-0103",
        "role": "nurse",
    },
    {
        "full_name": "Marcus Wright (Laboratory)",
        "email": "lab@aurex.com",
        "phone_number": "555-0104",
        "role": "laboratory",
    },
    {
        "full_name": "Priya Patel (Pharmacy)",
        "email": "pharmacy@aurex.com",
        "phone_number": "555-0105",
        "role": "pharmacy",
    },
    {
        "full_name": "Alex Martinez (Front Desk)",
        "email": "frontdesk@aurex.com",
        "phone_number": "555-0106",
        "role": "front_desk",
    },
    {
        "full_name": "Karen O'Connor (Insurance)",
        "email": "insurance@aurex.com",
        "phone_number": "555-0107",
        "role": "insurance",
    },
    {
        "full_name": "David Sterling (Department Head)",
        "email": "department@aurex.com",
        "phone_number": "555-0108",
        "role": "department",
    },
    {
        "full_name": "System Administrator",
        "email": "admin@aurex.com",
        "phone_number": "555-0109",
        "role": "administrator",
    },
]


def seed_database():
    """Seeds or updates demo accounts in the MySQL database."""
    db = SessionLocal()
    try:
        print("[*] Seeding AUREX HMS test accounts...")
        hashed_password = hash_password(DEMO_PASSWORD)

        for account in SEED_ACCOUNTS:
            user = db.query(User).filter(User.email == account["email"]).first()
            if user:
                user.full_name = account["full_name"]
                user.phone_number = account["phone_number"]
                user.role = account["role"]
                user.password_hash = hashed_password
                user.is_active = True
                print(f"  [+] Updated existing user: {account['email']} ({account['role']})")
            else:
                user = User(
                    full_name=account["full_name"],
                    email=account["email"],
                    phone_number=account["phone_number"],
                    role=account["role"],
                    password_hash=hashed_password,
                    is_active=True,
                )
                db.add(user)
                print(f"  [+] Created new user: {account['email']} ({account['role']})")

        db.commit()
        print("\n[SUCCESS] Seeding complete!")
        print(f"[*] All demo accounts configured with password: '{DEMO_PASSWORD}'")
    except Exception as exc:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
