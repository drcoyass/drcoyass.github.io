import os
import google.generativeai as genai

with open(".env", "r") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            os.environ["GEMINI_API_KEY"] = line.strip().split("=")[1].strip('"\'')

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)
