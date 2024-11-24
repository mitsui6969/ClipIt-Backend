from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
from pydantic import BaseModel
from transformers import CLIPProcessor, CLIPModel
import torch
import torch.nn.functional as F
import time
import os
import shutil
from fastapi.middleware.cors import CORSMiddleware


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


#/ranking_{theme_id}のレスポンス
class rankingData(BaseModel):
    similarity: float
    rank: int
    img_id: int
class rankingResponse(BaseModel):
    results: list[rankingData]


#/uploadのレスポンス
class uploadResponse(BaseModel):
    similarity: float
    rank: int


#/themeのレスポンス
class themeData(BaseModel):
    rank: int
    theme_id: int
    similarity: int
    img_id: int

class themeResponse(BaseModel):
    results: list[themeData]

def generate_id():
    timestamp = int(time.time() * 1000)
    return str(timestamp)



@app.get("/")
async def read_root():
    return {"message": "Hello, Clipit!"}



@app.get("/ranking_{theme_id}", response_model=rankingResponse)

async def response_ranking(theme_id: int):
    results = [
        
            rankingData(
                similarity = 20+1,
                rank = 1,
                img_id = 1732467566068+1
            )
        for i in range(10)
    ]
    return rankingResponse(results=results)


@app.get("/theme", response_model=themeResponse)
async def response_theme():
    results = [
            themeData(
                rank = 1,
                theme_id = 1,
                similarity = 20+1,
                img_id = 1732467566068
            )
        for i in range(10)
    ]
    return themeResponse(results=results)


@app.post("/upload", response_model=uploadResponse)

async def response_similarity(file: UploadFile = File(...)):

    file_name = generate_id() + ".jpeg"
    file_path = os.path.join(IMG_DIR, file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        image = Image.open(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file")

    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    inputs = processor(text=["a photo of a cat"], images=image, return_tensors="pt", padding=True)

    outputs = model(**inputs)
    image_embeds = outputs.image_embeds
    text_embeds = outputs.text_embeds

    cosine_similarity = F.cosine_similarity(image_embeds, text_embeds)
    similarity_percentage = cosine_similarity.item() * 100

    rank = int(similarity_percentage // 10)
    return uploadResponse(similarity=similarity_percentage, rank=rank)
