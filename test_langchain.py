import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
models_to_test = [
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "gemini-pro",
    "gemini-2.5-pro",
    "gemini-2.0-flash"
]

for m in models_to_test:
    try:
        llm = ChatGoogleGenerativeAI(model=m)
        print(f"{m}:", llm.invoke("Hi").content.strip())
    except Exception as e:
        print(f"{m} Failed:", e)
