from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import redis_client
import logging
import logstash
import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel

# Configure logging
host = 'logstash'
test_logger = logging.getLogger('python-logstash-logger')
test_logger.setLevel(logging.INFO)
test_logger.addHandler(logstash.TCPLogstashHandler(host, 5000, version=1))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logstash.TCPLogstashHandler(host, 5000, version=1))

app = FastAPI(title="URL Analytics Platform")

# Vertex AI Setup (Try/Except to allow local run without creds if needed)
try:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
    vertexai.init(project=PROJECT_ID, location="us-central1")
    model = GenerativeModel("gemini-pro")
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
        prompt = f"""
        Analyze the following URL: {url}
        1. Categorize it (e.g., Tech, News, Shopping, Social).
        2. Provide a very short summary (max 10 words) of what this site likely is.
        Return ONLY a JSON object like: {{"category": "CategoryName", "summary": "Short summary here"}}
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
