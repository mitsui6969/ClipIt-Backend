import os
import requests
import logging
from fastapi import FastAPI,HTTPException, Form,Depends
from pydantic import BaseModel,ValidationError
from sqlalchemy import create_engine,text
from sqlalchemy.orm import  sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware
from .models import themeTable, similarityTable 

DB_URL = os.getenv("DB_URL")
CLIP_URL = os.getenv("CLIP_URL")
THEME_IMG_URL = os.getenv("THEME_IMG_URL")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

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
def response_ranking(theme_id: int, db: Session = Depends(get_db)):
    try:
        if not theme_id:
            raise HTTPException(status_code=400, detail="request error. theme_idが必要です")
        
        logging.info(f"ranking_{theme_id}: theme_id:{theme_id}")  
        theme = db.query(themeTable).filter(themeTable.theme_id == theme_id).first()
        theme_name = theme.theme
        similarity_sort= (
            db.query(similarityTable)
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

    except ValidationError as e:
        logging.info(F"Validation error:{e}")
        raise HTTPException(status_code=422, detail=f"Validation error: {e}")
    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception  as e:
        logging.info(F"Server error:{e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")




@app.get("/theme", response_model=themeResponse)
def response_theme(db: Session = Depends(get_db)):
    try:
        logging.info(f"/theme")  

        themes = db.query(themeTable).all()
        theme_data = []

        for theme in themes:
            similarity_sort = (
                db.query(similarityTable)
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
                    image_url= THEME_IMG_URL
                ))

        return themeResponse(results=theme_data)

    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logging.info(F"Server error:{e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")



@app.post("/upload", response_model=uploadResponse)

def response_similarity(img_url: str = Form(...), theme_id: int = Form(...),db: Session = Depends(get_db)):

    try:
        if not img_url or not theme_id:
            raise HTTPException(status_code=400, detail="request error. img_urlとtheme_idが必要です")   
        logging.info(f"/upload img_url:{img_url}, theme_id: {theme_id}")  
        
        theme = db.query(themeTable).filter(themeTable.theme_id == theme_id).first()

        form_data = {
            "theme": theme.theme,
            "img_url": img_url
        }

        logging.info(f"form_data:{form_data}")  
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        response = requests.post(CLIP_URL,  headers= headers,data=form_data)
        data = response.json()
        logging.info(f"clip:{data}")
        similarity = float(data.get("similarity", 0))
        logging.info(f"similarity:{similarity}")  



        new_similarity = similarityTable(img_url=img_url, theme_id=theme_id, similarity=similarity)
        db.add(new_similarity)
        db.commit()

        similarity_sort= (
            db.query(similarityTable)
            .filter(similarityTable.theme_id == theme_id)
            .order_by(similarityTable.similarity.desc())
            .all()
        )
        rank = None
        for i, tabel in enumerate(similarity_sort, 1): 
            if tabel.similarity < similarity:
                break
            rank = i


        return uploadResponse(similarity=similarity, rank = rank)
    except ValidationError as e:
        logging.info(F"Validation error:{e}")
        raise HTTPException(status_code=422, detail=f"Validation error: {e}")
    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception  as e:
        logging.info(F"Server error:{e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@app.post("/register_theme")
def register_theme(theme: str = Form(...),db: Session = Depends(get_db)):

    try:
        if not theme:
            raise HTTPException(status_code=400, detail="request error. themeが必要です") 

        theme = theme.encode('utf-8').decode('utf-8')
        logging.info(f"register_theme:{theme}")  
        db.execute(text("SET client_encoding TO 'UTF8'"))
        new_theme = themeTable(theme=theme)
        db.add(new_theme)
        db.commit() 
        return True

    except ValidationError as e:
        logging.info(F"Validation error:{e}")
        raise HTTPException(status_code=422, detail=f"Validation error: {e}")
    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception  as e:
        logging.info(F"Server error:{e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
