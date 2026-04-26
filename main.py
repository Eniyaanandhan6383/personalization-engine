from fastapi import FastAPI
from database import engine, Base
from routers import auth, track, recommend, ads, why_this

# Create tables safely — won't crash if DB is unreachable
try:
    Base.metadata.create_all(bind=engine)
    print("[DB] Tables created/verified OK")
except Exception as e:
    print(f"[DB] Warning: Could not connect to DB on startup: {e}")
    print("[DB] App will still start — DB connects per request")

app = FastAPI(title="Personalization Engine", version="1.0.0")

app.include_router(auth.router)
app.include_router(track.router)
app.include_router(recommend.router)
app.include_router(ads.router)
app.include_router(why_this.router)

@app.get("/")
def root():
    return {"message": "Personalization Engine is live", "status": "ok"}