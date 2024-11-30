from fastapi import FastAPI,HTTPException, Form
from pydantic import BaseModel
import os
import requests
import logging
from sqlalchemy import create_engine,text
from sqlalchemy.orm import  sessionmaker
from fastapi.middleware.cors import CORSMiddleware
from .models import themeTable, similarityTable 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL,  connect_args={"client_encoding": "utf8"} ,echo=True)
Session = sessionmaker(bind=engine)



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class rankingData(BaseModel):
    similarity: float
    rank: int
    image_url: str
    theme_name: str
    theme_id: int
    
class rankingResponse(BaseModel):
    results: list[rankingData]


class uploadResponse(BaseModel):
    similarity: float
    rank: int


class themeData(BaseModel):
    rank: int
    theme_id: int
    theme_name: str
    similarity: float
    image_url: str

class themeResponse(BaseModel):
    results: list[themeData]




@app.get("/")
def read_root():
    return {"message": "Hello, Clipit!"}

@app.get("/ranking_{theme_id}", response_model=rankingResponse)
def response_ranking(theme_id: int):

    session  = Session()
    theme = session.query(themeTable).filter(themeTable.theme_id == theme_id).first()
    theme_name = theme.theme

    similarity_sort= (
        session.query(similarityTable)
        .filter(similarityTable.theme_id ==theme_id)
        .order_by(similarityTable.similarity.desc())
        .limit(10)
        .all()
    )
    ranking_data = []
    for rank, similarity in enumerate(similarity_sort, start=1):
        ranking_data.append(rankingData(
            similarity=similarity.similarity,
            theme_name=theme_name,
            rank=rank,
            theme_id = similarity.theme_id,
            image_url= similarity.img_url
        ))
    
    return rankingResponse(results=ranking_data)






@app.get("/theme", response_model=themeResponse)
def response_theme():
    session  = Session()

    themes = session.query(themeTable).all()
    
    theme_data = []
    for theme in themes:
        similarity_sort = (
            session.query(similarityTable)
            .filter(similarityTable.theme_id == theme.theme_id)
            .order_by(similarityTable.similarity.desc())
            .first() 
        )
        if similarity_sort:
            theme_data.append(themeData(
                rank=1,
                theme_id=theme.theme_id,
                theme_name=theme.theme,
                similarity=similarity_sort.similarity,
                image_url= similarity_sort.img_url
            ))
        else:
            theme_data.append(themeData(
                rank=1,
                theme_id=theme.theme_id,
                theme_name=theme.theme,
                similarity=0.0,
                image_url= "https://firebasestorage.googleapis.com/v0/b/clipit-2e405.firebasestorage.app/o/test.jpg?alt=media&token=67a3500c-b0d9-481c-a2d8-309ee1a1fc16"
            ))
    return themeResponse(results=theme_data)


@app.post("/upload", response_model=uploadResponse)

def response_similarity(img_url: str = Form(...), theme_id: int = Form(...)):
    logging.info("upload")
    logging.info(f"file:{img_url}, theme: {theme_id}")  
    
    session  = Session()

    theme = session.query(themeTable).filter(themeTable.theme_id == theme_id).first()
        

    logging.info(f"file:{img_url}, theme: {theme.theme}")  

    form_data = {
        "theme": theme.theme,
        "img_url": img_url

    }
    logging.info(f"form_data:{form_data}")  
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

    response = requests.post("https://clipit-imgserver.onrender.com/upload",  headers= headers,data=form_data)
    data = response.json()
    logging.info(data)
    similarity = float(data.get("similarity", 0))
    logging.info(f"similarity:{similarity}")  



    new_similarity = similarityTable(img_url=img_url, theme_id=theme_id, similarity=similarity)
    session.add(new_similarity)
    session.commit()

    similarity_sort= (
        session.query(similarityTable)
        .filter(similarityTable.theme_id ==theme_id)
        .order_by(similarityTable.similarity.desc())
        .all()
    )
    rank = None
    for i, db in enumerate(similarity_sort, 1): 
        if db.similarity < similarity:
            rank = i
            break

    return uploadResponse(similarity=similarity, rank = rank)


@app.post("/register_theme")
def register_theme(theme: str = Form(...)):
    logging.info(f"register_theme:{theme}")  
    session  = Session()
    session.execute(text("SET client_encoding TO 'UTF8'"))
    new_theme = themeTable(theme=theme)
    session.add(new_theme)
    session.commit()  
    return True
