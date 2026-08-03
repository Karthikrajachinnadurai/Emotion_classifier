from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from . import models, database, ml, dependencies
from .routers import auth, predict, gamification, speech
from contextlib import asynccontextmanager

import pymysql

# Auto-create MySQL database if using pymysql
if "pymysql" in database.DATABASE_URL:
    try:
        connection = pymysql.connect(host='localhost', port=3306, user='root', password='root')
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS mental_health_db")
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Error creating database: {e}")

# Create DB tables
models.Base.metadata.create_all(bind=database.engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading ML components...")
    ml.init_ml()
    print("ML components loaded.")
    yield
    print("Shutting down...")

app = FastAPI(
    title="AI Mental Health Assistant API",
    description="Backend API for Emotion Detection and Gamification",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(gamification.router)
app.include_router(speech.router)  # Speech-to-Text — isolated, does not affect other routes

@app.get("/health")
def health_check(db: database.SessionLocal = Depends(dependencies.get_db)):
    db_connected = False
    try:
        db.execute("SELECT 1")
        db_connected = True
    except:
        pass
        
    return {
        "status": "ok",
        "db_status": "connected" if db_connected else "disconnected",
        "model_loaded": ml.model is not None,
        "whisper_loaded": ml.whisper_model is not None
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Mental Health Assistant API"}
