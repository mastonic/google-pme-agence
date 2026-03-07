import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
    print("PRO:", llm.invoke("Hi"))
except Exception as e:
    print("PRO Failed:", e)

try:
    llm2 = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    print("FLASH:", llm2.invoke("Hi"))
except Exception as e:
    print("FLASH Failed:", e)
    
try:
    llm3 = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")
    print("PRO LATEST:", llm3.invoke("Hi"))
except Exception as e:
    print("PRO LATEST Failed:", e)
