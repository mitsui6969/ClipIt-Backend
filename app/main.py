from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from PIL import Image
from pydantic import BaseModel
import time
import os
import shutil
from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import requests
from fastapi.middleware.cors import CORSMiddleware
from .models import themeTable, similarityTable 

DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL, echo=True)
Session = sessionmaker(bind=engine)



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


IMG_DIR = "./upload_img"
os.makedirs(IMG_DIR, exist_ok=True)


class rankingData(BaseModel):
    similarity: float
    theme_name: str
    rank: int
    img_url: str
    
class rankingResponse(BaseModel):
    results: list[rankingData]


class uploadResponse(BaseModel):
    similarity: float
    rank: float


class themeData(BaseModel):
    rank: int
    theme_id: int
    theme_name: str
    similarity: float
    img_url: str

class themeResponse(BaseModel):
    results: list[themeData]

def generate_id():
    timestamp = int(time.time() * 1000)
    return str(timestamp)


@app.get("/")
def read_root():
    return {"message": "Hello, Clipit!"}



@app.get("/ranking_{theme_id}", response_model=rankingResponse)
def response_ranking(theme_id: int):

    session  = Session()
    theme = session.query(themeTable).filter(themeTable.theme_id == theme_id).first()
    similarities = session.query(similarityTable).filter(similarityTable.theme_id == theme_id).all()
    theme_name = theme.theme

    ranking_data = []
    for rank, similarity in enumerate(similarities, start=1):
        ranking_data.append(rankingData(
            similarity=similarity.similarity,
            theme_name=theme_name,
            rank=3,
            img_url=f"https://clipit-imgserver.onrender.com//upload_img/{similarity.img_id}.jpg" 
        ))
    
    return rankingResponse(results=ranking_data)


@app.get("/theme", response_model=themeResponse)
def response_theme():
    session  = Session()

    themes = session.query(themeTable).all()
    
    theme_data = []
    for theme in themes:
        similarities = session.query(similarityTable).filter(similarityTable.theme_id == theme.theme_id).all()
        
        for similarity in similarities:
            theme_data.append(themeData(
                rank=3,
                theme_id=theme.theme_id,
                theme_name=theme.theme,
                similarity=similarity.similarity,
                img_url=f"https://clipit-imgserver.onrender.com//upload_img/{similarity.img_id}.jpg"             
                ))
    
    return themeResponse(results=theme_data)


@app.post("/upload", response_model=uploadResponse)

def response_similarity(file: UploadFile = File(...), theme_id: int = Form(...)):
    print("upload")
    print(f"file:{file.filename}, theme: {theme_id}")  
    
    session  = Session()

    theme = session.query(themeTable).filter(themeTable.theme_id == theme_id).first()
    print(f"file:{file.filename}, theme: {theme.theme}")  

    files = {
        "file": (file.filename, file.file, file.content_type)
    }
    form_data = {
        "theme": theme.theme,
    }

    response = requests.post("https://clipit-imgserver.onrender.com/upload", files=files, data=form_data)
    data = response.json()
    similarity = float(data.get("similarity", 0))
    img_id = float(data.get("img_id", 0))
    print(f"similarity:{similarity} theme_id: {theme_id} img_id={img_id}")  
    new_similarity = similarityTable(img_id=img_id, theme_id=theme_id, similarity=similarity)
    session.add(new_similarity)
    return uploadResponse(similarity=similarity, rank = 2)
