import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

print("KEY =", os.environ.get("GEMINI_API_KEY"))
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

for m in genai.list_models():
    if "generateContent" in getattr(m, "supported_generation_methods", []):
        print(m.name)
