import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

SQLALCHEMY_DATABASE_URL = "sqlite:///./hitl.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def mock_ai_extraction(filename):
    return {
        "invoice_number": "INV-2023-001",
        "date": "2023-10-12",
        "total_amount": "150.00",
        "vendor": "Unknown Vendor"
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    extraction = mock_ai_extraction(file.filename)
    db_doc = Document(filename=file.filename, ai_extraction=extraction, status="pending")
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return {"id": db_doc.id, "extraction": extraction}

@app.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    return db.query(Document).filter(Document.status == "pending").all()

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
    
    db.commit()
    return {"status": "success", "message": "Correction saved & Document validated"}