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
API_KEYS_STR = os.getenv("OPENROUTER_API_KEYS", "")
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
    if not API_KEYS:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEYS not set in environment variables.")
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

EXA_API_KEY = os.getenv("EXA_API_KEY", "")

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

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

@app.get("/search/youtube")
def tavily_youtube_search(query: str = Query(..., description="Search query"), max_results: int = 5):
    """
    Search YouTube videos using Tavily API.
    """
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not set in environment variables."}
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
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not set in environment variables."}
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
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not set in environment variables."}
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
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not set in environment variables."}
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
