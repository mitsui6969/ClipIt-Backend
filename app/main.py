from fastapi import FastAPI

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



@app.post("/upload")
async def read_user_me():
    return {"user_id": "the current user"}

