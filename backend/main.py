from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
import io
from fastapi.staticfiles import StaticFiles
import os

# For file processing
from typing import List
from PIL import Image
import pytesseract
import PyPDF2
import docx

app = FastAPI()

# Get API keys from environment variables
API_KEYS_STR = "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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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"
API_KEYS = [key.strip() for key in API_KEYS_STR.split(",") if key.strip()]

# Get allowed origins from environment variables
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,http://localhost:8080,http://127.0.0.1:8080")
ALLOWED_ORIGINS_LIST = [origin.strip() for origin in ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# ✅ Input schema
class PromptInput(BaseModel):
    prompt: str
    model: str

class ChainRequest(BaseModel):
    prompt: str
    models: list[str]

# ✅ Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running"}

# ✅ Main endpoint to send prompt and receive model response
@app.post("/ask")
def ask_model(data: PromptInput):
    last_error = None

    # Shuffle keys to distribute load (optional)
    keys = API_KEYS.copy()
    random.shuffle(keys)
    
    print(f"🔑 Trying {len(keys)} API keys for request...")

    for i, api_key in enumerate(keys, 1):
        print(f"🔑 Attempt {i}/{len(keys)} with key: {api_key[:10]}...{api_key[-4:]}")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        print(f"Trying API key: {api_key[:10]}...{api_key[-4:]}")
        print(f"Headers: {headers}")
        payload = {
            "model": data.model,
            "messages": [
                {"role": "user", "content": data.prompt}
            ]
        }
        try:
            response = requests.post(BASE_URL, headers=headers, json=payload, timeout=30)
            print(f"Status code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            last_error = f"❌ API key ending in ...{api_key[-8:]} failed: Network error - {str(e)}"
            print(f"Network error with API key, trying next key...")
            continue

        if response.status_code == 200:
            try:
                result = response.json()
                return {
                    "model": data.model,
                    "response": result["choices"][0]["message"]["content"]
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail="Invalid response format: " + str(e))

        # Rotate on 429, 403, 401, or any other error
        elif response.status_code in (429, 403, 401, 400, 500, 502, 503, 504):
            last_error = f"❌ API key ending in ...{api_key[-8:]} failed: {response.status_code} - {response.text}"
            print(f"API key failed with status {response.status_code}, trying next key...")
            continue
        else:
            # For any other unexpected status code, also try next key
            last_error = f"❌ API key ending in ...{api_key[-8:]} failed: {response.status_code} - {response.text}"
            print(f"Unexpected status {response.status_code}, trying next key...")
            continue

    # All keys failed
    raise HTTPException(status_code=429, detail=f"All keys exhausted. Last error: {last_error or 'Unknown error'}")

@app.post("/chain")
def chain_models(data: ChainRequest):
    last_error = None
    current_prompt = data.prompt
    responses = []

    for model_id in data.models:
        keys = API_KEYS.copy()
        random.shuffle(keys)
        for api_key in keys:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": current_prompt}
                ]
            }
            try:
                response = requests.post(BASE_URL, headers=headers, json=payload, timeout=30)
            except requests.exceptions.RequestException as e:
                last_error = f"API key ending in ...{api_key[-8:]} failed: Network error - {str(e)}"
                print(f"Chain: Network error with API key, trying next key...")
                continue
            if response.status_code == 200:
                try:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    responses.append({"model": model_id, "response": content})
                    current_prompt = content  # Pass output to next model
                    break
                except Exception as e:
                    raise HTTPException(status_code=500, detail="Invalid response format: " + str(e))
            elif response.status_code in (429, 403, 401, 400, 500, 502, 503, 504):
                last_error = f"API key ending in ...{api_key[-8:]} failed: {response.status_code} - {response.text}"
                print(f"Chain: API key failed with status {response.status_code}, trying next key...")
                continue
            else:
                # For any other unexpected status code, also try next key
                last_error = f"API key ending in ...{api_key[-8:]} failed: {response.status_code} - {response.text}"
                print(f"Chain: Unexpected status {response.status_code}, trying next key...")
                continue
        else:
            responses.append({"model": model_id, "response": f"Error: All keys exhausted for {model_id}. Last error: {last_error or 'Unknown error'}"})
            current_prompt = data.prompt

    return {"responses": responses}

@app.post("/upload")
def upload_files(files: List[UploadFile] = File(...)):
    extracted_texts = []
    for file in files:
        if file.filename is None:
            continue
        filename = file.filename.lower()
        content = file.file.read()
        text = ""
        try:
            if filename.endswith('.pdf'):
                reader = PyPDF2.PdfReader(io.BytesIO(content))
                for page in reader.pages:
                    text += page.extract_text() or ""
            elif filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                image = Image.open(io.BytesIO(content))
                text = pytesseract.image_to_string(image)
            elif filename.endswith(('.doc', '.docx')):
                doc = docx.Document(io.BytesIO(content))
                text = "\n".join([para.text for para in doc.paragraphs])
            else:
                text = content.decode(errors='ignore')
        except Exception as e:
            text = f"[Error processing {filename}: {str(e)}]"
        extracted_texts.append({"filename": file.filename, "text": text})
    return {"files": extracted_texts}

EXA_API_KEY = "79a27d38-21af-4824-ac2b-f111772390f0"

@app.get("/search/web")
def exa_web_search(query: str = Query(..., description="Search query")):
    if not EXA_API_KEY:
        return {"error": "EXA_API_KEY not set in environment variables."}
    url = "https://api.exa.ai/search"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {EXA_API_KEY}"
    }
    payload = {
        "query": query,
        "numResults": 5
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

TAVILY_API_KEY = "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"

@app.get("/search/youtube")
def tavily_youtube_search(query: str = Query(..., description="Search query"), max_results: int = 5):
    """
    Search YouTube videos using Tavily API.
    """
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    payload = {
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
        "max_results": max_results,
        "include_sources": True,
        "search_type": "youtube"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print("Tavily YouTube response:", response.text)  # Debug print
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/search/reddit")
def tavily_reddit_search(query: str = Query(..., description="Search query"), max_results: int = 5):
    """
    Search Reddit posts using Tavily API.
    """
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    payload = {
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
        "max_results": max_results,
        "include_sources": True,
        "search_type": "reddit"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print("Tavily Reddit response:", response.text)  # Debug print
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/search/academic")
def tavily_academic_search(query: str = Query(..., description="Search query"), max_results: int = 5):
    """
    Search academic papers using Tavily API.
    """
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    payload = {
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
        "max_results": max_results,
        "include_sources": True,
        "search_type": "academic"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print("Tavily Academic response:", response.text)  # Debug print
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/search/crypto")
def tavily_crypto_search(query: str = Query(..., description="Search query"), max_results: int = 5):
    """
    Search crypto news using Tavily API.
    """
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    payload = {
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
        "max_results": max_results,
        "include_sources": True,
        "search_type": "crypto"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print("Tavily Crypto response:", response.text)  # Debug print
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Serve React build files (dist) as static files
frontend_dist = os.path.join(os.path.dirname(__file__), "../dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Use Render's PORT environment variable, fallback to 8000 for local development
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    print(f"🌐 Environment: PORT={os.getenv('PORT', 'Not set (using 8000)')}")
    uvicorn.run(app, host="0.0.0.0", port=port) 
