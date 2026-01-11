import shutil
import os
import datetime
import json
import joblib
from typing import List, Optional

# Framework Web
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # <--- AJOUTÉ
from pydantic import BaseModel

# Base de données
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# NOS MODULES (Vos fichiers existants)
from extraction_engine import extract_invoice_data 
from train_model import train as train_pipeline     

# --- CONFIGURATION DB ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./hitl.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODÈLES DB ---
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="pending") 
    ai_extraction = Column(JSON) 

class Correction(Base):
    __tablename__ = "corrections"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer)
    corrected_data = Column(JSON) 
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    time_taken = Column(Integer) 

Base.metadata.create_all(bind=engine)

class CorrectionSchema(BaseModel):
    document_id: int
    corrected_data: dict
    time_taken: int

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION DOSSIER UPLOADS (POUR L'AFFICHAGE) ---
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# On rend le dossier "uploads" accessible via http://localhost:8000/uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- LOGIQUE INTELLIGENTE ---
MODEL_PATH = "model_hitl.pkl"

def smart_extraction(file_path, filename):
    data = extract_invoice_data(file_path)
    
    if os.path.exists(MODEL_PATH):
        try:
            print("🤖 Modèle IA détecté...")
            model = joblib.load(MODEL_PATH)
            skills_found = data.get("skills", "")
            
            # Prediction simple
            predicted_role = model.predict([skills_found])[0]
            data["predicted_role"] = predicted_role
            
        except Exception as e:
            print(f"⚠️ L'IA n'a pas pu prédire : {e}")
    else:
        print("ℹ️ Mode Cold Start.")

    return data

# --- ROUTES API ---

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Sauvegarder dans 'uploads' au lieu de 'temp_'
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 2. Extraction
    extraction = smart_extraction(file_location, file.filename)
    
    # 3. Sauvegarde DB (On ne supprime PAS le fichier pour pouvoir l'afficher)
    db_doc = Document(filename=file.filename, ai_extraction=extraction, status="pending")
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    return {"id": db_doc.id, "extraction": extraction}

@app.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.upload_date.desc()).all()

@app.post("/validate")
def validate_correction(correction: CorrectionSchema, db: Session = Depends(get_db)):
    db_corr = Correction(
        document_id=correction.document_id,
        corrected_data=correction.corrected_data,
        time_taken=correction.time_taken
    )
    db.add(db_corr)

    doc = db.query(Document).filter(Document.id == correction.document_id).first()
    if doc:
        doc.status = "validated"
        doc.ai_extraction = correction.corrected_data
    
    db.commit()
    return {"status": "success"}

@app.post("/retrain")
def retrain_endpoint():
    try:
        train_pipeline() 
        return {"status": "success", "message": "Modèle ré-entraîné avec succès !"}
    except Exception as e:
        print(f"Erreur entrainement: {e}")
        raise HTTPException(status_code=500, detail=str(e))