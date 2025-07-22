
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import base64
import os
from dotenv import load_dotenv

load_dotenv()  # This loads the .env file into environment variables
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

with open("config/prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

client = OpenAI()

@app.post("/ask")
async def ask_ai(
    question: str = Form(...),
    class_level: str = Form(...),
    board: str = Form(...),
    language: str = Form(...)
):
    context_prompt = (
        f"Student is in {class_level} under {board} board."
        f"The preferred language style is {language}."
        f"Answer the following question in a way that matches the student's maturity level and preferred language style."
        f"Question: {question}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context_prompt}
        ]
    )

    return {"response": response.choices[0].message.content}

@app.post("/upload-image")
async def image_input(file: UploadFile = File(...)):
    content = await file.read()
    img_b64 = base64.b64encode(content).decode("utf-8")
    return {"status": "Image received", "preview": img_b64[:100]}

@app.post("/voice")
async def voice_input(file: UploadFile = File(...)):
    filepath = f"static/uploads/{file.filename}"
    with open(filepath, "wb") as f:
        f.write(await file.read())
    return {"text": "Transcribed question from audio goes here"}