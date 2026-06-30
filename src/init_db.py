# src/init_db.py
import datetime
from src.core.database import engine, SessionLocal
from src.models import Base, User, ViolationReport
from src.core.security import PasswordHasher

def init_db():
    print("Dropping existing database tables (if any) to apply NVARCHAR types...")
    Base.metadata.drop_all(bind=engine)
    print("Initializing database tables...")
    # Create all tables in MSSQL
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    db = SessionLocal()
    try:
        # Check if users already exist to avoid duplicates
        if db.query(User).count() == 0:
            print("Seeding users...")
            users = [
                User(
                    username="citizen",
                    hashed_password=PasswordHasher.hash_password("password123"),
                    role="citizen",
                    full_name="CƯ DÂN"
                ),
                User(
                    username="authority",
                    hashed_password=PasswordHasher.hash_password("password123"),
                    role="authority",
                    full_name="CẢNH SÁT"
                ),
                User(
                    username="ai_system",
                    hashed_password=PasswordHasher.hash_password("password123"),
                    role="ai_system",
                    full_name="Hệ thống AI"
                )
            ]
            db.add_all(users)
            db.commit()
            print("Users seeded successfully.")

        # Check if violation reports exist
        if db.query(ViolationReport).count() == 0:
            print("Seeding initial mock violations...")
            # Sample coordinate points near central HCMC/Hanoi
            violations = [
                ViolationReport(
                    vehicle_plate="51H-678.90",
                    violation_type="Đỗ xe đè vỉa hè",
                    latitude=10.7745,
                    longitude=106.7025,
                    reporter_role="ai_system",
                    reporter_name="Hệ thống AI",
                    status="pending",
                    duration_seconds=320,
                    image_url="/media/test3.webp",
                    violation_time=datetime.datetime.utcnow() - datetime.timedelta(hours=2)
                ),
                ViolationReport(
                    vehicle_plate="29D-567.89",
                    violation_type="Đỗ khu vực biển cấm",
                    latitude=10.7760,
                    longitude=106.7030,
                    reporter_role="ai_system",
                    reporter_name="Camera AI Số #2 - Nguyễn Huệ",
                    status="rejected",
                    duration_seconds=900,
                    image_url="/media/test4.jpg",
                    violation_time=datetime.datetime.utcnow() - datetime.timedelta(days=1)
                ),
                ViolationReport(
                    vehicle_plate="72A-888.88",
                    violation_type="Đỗ xe đè vỉa hè",
                    latitude=10.7712,
                    longitude=106.6980,
                    reporter_role="citizen",
                    reporter_name="CƯ DÂN",
                    status="rejected",
                    duration_seconds=0,
                    image_url="/media/annotated_test2.jpg",
                    violation_time=datetime.datetime.utcnow() - datetime.timedelta(hours=5)
                ),
                ViolationReport(
                    vehicle_plate="43B-999.99",
                    violation_type="Đỗ song song đỗ kép",
                    latitude=10.7758,
                    longitude=106.7018,
                    reporter_role="citizen",
                    reporter_name="CƯ DÂN",
                    status="pending",
                    duration_seconds=0,
                    image_url="/media/test1.png",
                    violation_time=datetime.datetime.utcnow() - datetime.timedelta(minutes=45)
                )
            ]
            db.add_all(violations)
            db.commit()
            print("Violation reports seeded successfully.")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    init_db()
