import redis
import os
import hashlib

# Get Redis connection details from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Redis client
# decode_responses=True ensures we get strings back, not bytes
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def generate_short_code(url: str, length: int = 6) -> str:
    """Generate a deterministic short code for a URL using MD5 hash."""
    hash_object = hashlib.md5(url.encode())
    return hash_object.hexdigest()[:length]

def save_url(url: str) -> str:
    """Save URL to Redis and return short code."""
    short_code = generate_short_code(url)
    
    # Store mapping: short_code -> original_url
    r.set(short_code, url)
    
    # Invalidate old insights to ensure fresh analysis
    r.delete(f"insights:{short_code}")
    
    # Initialize click count
    if not r.exists(f"stats:{short_code}"):
        r.set(f"stats:{short_code}", 0)
        
    return short_code

def get_original_url(short_code: str) -> str:
    """Retrieve original URL from Redis."""
    return r.get(short_code)

def increment_visits(short_code: str):
    """Increment visit counter for the short code."""
    r.incr(f"stats:{short_code}")

def save_ai_insights(short_code: str, insights: dict):
    """Save AI analysis (category, summary) to Redis as a hash."""
    key = f"insights:{short_code}"
    r.hset(key, mapping=insights)

def get_stats(short_code: str) -> dict:
    """Get visit count and AI insights for the short code."""
    visits = r.get(f"stats:{short_code}")
    insights = r.hgetall(f"insights:{short_code}")
    
    return {
        "visits": int(visits) if visits else 0,
        "ai_insights": insights if insights else None
    }
