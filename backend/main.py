from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
import openai
import os
import time
import asyncio
from langdetect import detect
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()

# Allow CORS from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Telegram message sender
def notify_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing Telegram credentials.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=data)
        print("Telegram Response:", response.text)
    except Exception as e:
        print("Error sending Telegram message:", e)

@app.get("/")
def read_root():
    return {"message": "Backend is running"}

# Test endpoint to send a message
@app.get("/send-test")
def send_test():
    test_message = "✅ Test message from your TikTok Tracker bot is working."
    notify_telegram(test_message)
    return {"status": "sent", "message": test_message}

# Detect if caption is English
def is_english(text):
    try:
        return detect(text) == "en"
    except:
        return False

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def classify_caption(caption):
    prompt = f"""
    Classify the following TikTok content into one of the following categories:
    - News
    - Event
    - Phenomenon

    Content:
    {caption}

    Reply with just one word.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("[ERROR] classify_caption:", str(e))
        return "Unknown"

def summarize_caption(caption):
    prompt = f"Summarize this TikTok caption in a few words: {caption}"
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("[ERROR] summarize_caption:", str(e))
        return "No summary"



# TikTok analysis endpoint
@app.post("/analyze")
async def analyze(request: Request):
    try:
        data = await request.json()
        caption = data.get("caption", "")

        if not caption:
            return JSONResponse(content={"error": "No caption provided"}, status_code=400)

        english = is_english(caption)
        if not english:
            return {"status": "ignored", "reason": "Non-English content"}

        category = classify_caption(caption)
        summary = summarize_caption(caption)

        return {
            "status": "processed",
            "category": category,
            "summary": summary,
            "original_caption": caption
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Real TikTok captions loader (mocked JSON file from bot for now)
def fetch_real_tiktok_captions():
    try:
        with open("captions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# Run full auto-check every 1 minute
async def auto_tracker():
    while True:
        print("⏱️ Running TikTok Tracker check...")
        tiktok_captions = fetch_real_tiktok_captions()
        for caption in tiktok_captions:
            if not is_english(caption):
                continue
            category = classify_caption(caption)
            summary = summarize_caption(caption)
            alert = f"🚨 Viral Content Detected\n\n🧠 Summary: {summary}\n📌 Category: {category}\n📝 Original: {caption}"
            notify_telegram(alert)
            await asyncio.sleep(2)  # Slight delay between alerts
        await asyncio.sleep(60)  # Wait 1 minute between runs

@app.on_event("startup")
def startup_event():
    notify_telegram("🚀 TikTok Tracker backend just started.")
    asyncio.create_task(auto_tracker())
