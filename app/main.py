from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import redis_client
import logging
import logstash
import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from google.api_core.exceptions import GoogleAPICallError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests
from bs4 import BeautifulSoup

# Configure logging
host = 'logstash'
test_logger = logging.getLogger('python-logstash-logger')
test_logger.setLevel(logging.INFO)
test_logger.addHandler(logstash.TCPLogstashHandler(host, 5000, version=1))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logstash.TCPLogstashHandler(host, 5000, version=1))

app = FastAPI(title="URL Analytics Platform")

# Middleware for structured logging
import time
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        process_time = (time.time() - start_time) * 1000
        
        # Prepare structured log
        log_fields = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time, 2),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        # Log to Logstash (and console)
        logger.info("HTTP Request", extra=log_fields)
        
        return response

app.add_middleware(LoggingMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Vertex AI Setup (Try/Except to allow local run without creds if needed)
try:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
    vertexai.init(project=PROJECT_ID, location="us-central1")
    model = GenerativeModel("gemini-2.0-flash-exp")
    AI_ENABLED = True
except Exception as e:
    logger.warning(f"Vertex AI init failed: {e}. AI features disabled.")
    AI_ENABLED = False

class URLRequest(BaseModel):
    url: str

def analyze_url_task(short_code: str, url: str):
    """Background task to analyze URL with Gemini."""
    if not AI_ENABLED:
        return

    try:
        # Fetch page content
        try:
            page = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(page.content, 'html.parser')
            # Get text, remove excess whitespace, limit to 2000 chars
            page_text = " ".join(soup.get_text().split())[:2000]
        except Exception:
            page_text = "Could not fetch content. Analyze based on URL only."

        prompt = f"""
        Analyze the following website content from URL: {url}
        
        Website Text Content (Truncated):
        {page_text}
        
        1. Categorize it (e.g., Tech, News, Shopping, Social, etc).
        2. Provide a 2-sentence summary of what this specific page is about.
        
        Return ONLY a JSON object like: {{"category": "CategoryName", "summary": "Brief summary here"}}
        """
        response = model.generate_content(prompt)
        # Simple parsing (assuming model follows instructions, in prod we'd use robust parsing)
        import json
        text = response.text.strip()
        # Clean markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:-3]
        
        insights = json.loads(text)
        redis_client.save_ai_insights(short_code, insights)
        logger.info(f"AI Analysis for {short_code} complete: {insights}")

    except GoogleAPICallError as e:
        logger.warning(f"AI Analysis skipped for {short_code} (GCP API Error): {e.message if hasattr(e, 'message') else e}")
    except Exception as e:
        logger.error(f"AI Analysis failed for {short_code}: {e}")

@app.post("/shorten")
def shorten_url(request: URLRequest, background_tasks: BackgroundTasks):
    """Create a short URL."""
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        short_code = redis_client.save_url(request.url)
        logger.info(f"Shortened {request.url} to {short_code}")
        
        # Trigger AI analysis
        background_tasks.add_task(analyze_url_task, short_code, request.url)
        
        return {"short_code": short_code, "original_url": request.url}
    except Exception as e:
        logger.error(f"Error saving URL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/{short_code}")
def redirect_to_url(short_code: str):
    """Redirect to original URL."""
    url = redis_client.get_original_url(short_code)
    
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    # Async increment to not block the redirect too much (though Redis is fast)
    try:
        redis_client.increment_visits(short_code)
    except Exception as e:
        logger.error(f"Error incrementing stats for {short_code}: {e}")

    return RedirectResponse(url=url)

@app.get("/stats/{short_code}")
def get_url_stats(short_code: str):
    """Get analytics for a short URL."""
    url = redis_client.get_original_url(short_code)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    stats = redis_client.get_stats(short_code)
    return {
        "short_code": short_code,
        "original_url": url,
        "visits": stats["visits"],
        "ai_insights": stats["ai_insights"]
    }

@app.get("/health/ready")
def health_check():
    """Simple health check."""
    return {"status": "ok"}
