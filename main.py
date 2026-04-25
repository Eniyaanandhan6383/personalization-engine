from fastapi import FastAPI
from database import engine, Base
from routers import auth, track

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personalization Engine", version="1.0.0")

app.include_router(auth.router)
app.include_router(track.router)

@app.get("/")
def root():
    return {"message": "Personalization Engine is live", "status": "ok"}