from fastapi import FastAPI
from PIL import Image
import requests
from transformers import CLIPProcessor, CLIPModel
import torch
import torch.nn.functional as F


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, Clipit!"}


@app.get("/theme")

# class getTheme :

def twst():
    return {"item_id": item_id}


@app.post("/ranking_{theme_id}")

async def root():
    return {"message": "orld"}



@app.get("/upload")
async def read_user_me():
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    image = Image.open(requests.get(url, stream=True).raw)

    inputs = processor(text=["a photo of a cat"], images=image, return_tensors="pt", padding=True)

    outputs = model(**inputs)
    image_embeds = outputs.image_embeds  
    text_embeds = outputs.text_embeds  


    cosine_similarity = F.cosine_similarity(image_embeds, text_embeds)
    similarity_percentage = cosine_similarity.item() * 100

    print(f"一致度 : {similarity_percentage:.2f}%")
    return {"similarity": similarity_percentage}
