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
API_KEYS_STR = "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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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,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"
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
