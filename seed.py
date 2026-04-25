from database import SessionLocal, engine, Base
from models.models import User, BehaviorLog, UserProfile, Ad
from services.ml_engine import build_user_profile
from passlib.context import CryptContext
import uuid, json

Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    db = SessionLocal()

    # Clear existing seed data
    db.query(BehaviorLog).delete()
    db.query(UserProfile).delete()
    db.query(Ad).delete()
    db.query(User).filter(User.email == "seeduser@test.com").delete()
    db.commit()

    # Create demo user
    user = User(
        id=str(uuid.uuid4()),
        email="seeduser@test.com",
        password=pwd_context.hash("seed123"),
        api_key=str(uuid.uuid4())
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[SEED] Created user: {user.email} | id: {user.id}")

    # Create 20 behavior logs
    events = [
        ("click",  "c001", "tech",    1.0),
        ("click",  "c002", "tech",    1.0),
        ("watch",  "c003", "tech",    2.0),
        ("click",  "c001", "tech",    1.0),
        ("search", "c004", "tech",    1.0),
        ("click",  "c005", "tech",    1.0),
        ("watch",  "c006", "tech",    2.0),
        ("click",  "c007", "tech",    1.0),
        ("click",  "c008", "sports",  1.0),
        ("watch",  "c009", "sports",  2.0),
        ("click",  "c010", "sports",  1.0),
        ("click",  "c011", "finance", 1.0),
        ("watch",  "c012", "finance", 2.0),
        ("click",  "c013", "health",  1.0),
        ("click",  "c014", "health",  1.0),
        ("click",  "c015", "tech",    1.0),
        ("watch",  "c016", "tech",    2.0),
        ("click",  "c017", "sports",  1.0),
        ("click",  "c018", "finance", 1.0),
        ("click",  "c019", "tech",    1.0),
    ]

    for event_type, content_id, category, value in events:
        log = BehaviorLog(
            user_id=user.id,
            event_type=event_type,
            content_id=content_id,
            category=category,
            value=value
        )
        db.add(log)
    db.commit()
    print(f"[SEED] Created 20 behavior logs")

    # Seed ads table
    ads = [
        Ad(title="Learn AWS in 30 days",         category="tech",    url="https://example.com/aws",     body="Master cloud with hands-on labs"),
        Ad(title="GitHub Copilot Pro",            category="tech",    url="https://example.com/copilot", body="AI pair programmer for developers"),
        Ad(title="Nike Running Shoes Sale",       category="sports",  url="https://example.com/nike",    body="Up to 40% off this weekend"),
        Ad(title="Dream11 — Win Big Today",       category="sports",  url="https://example.com/d11",     body="Join 10 crore+ players"),
        Ad(title="Zerodha — Start Investing",     category="finance", url="https://example.com/zerodha", body="India's largest stock broker"),
        Ad(title="Groww Mutual Funds",            category="finance", url="https://example.com/groww",   body="Start SIP with just ₹100"),
        Ad(title="Cult.fit Membership",           category="health",  url="https://example.com/cult",    body="Workout, nutrition & more"),
        Ad(title="HealthifyMe Pro",               category="health",  url="https://example.com/hfm",     body="AI diet & fitness coach"),
    ]
    for ad in ads:
        db.add(ad)
    db.commit()
    print(f"[SEED] Created {len(ads)} ads")

    # Save user_id as plain string BEFORE closing session
    user_id_str = str(user.id)
    db.close()

    # Run ML engine to build profile
    print(f"[SEED] Building user profile...")
    build_user_profile(user_id_str)
    print(f"[SEED] Done. Login with: seeduser@test.com / seed123")

if __name__ == "__main__":
    seed()