
import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from google.api_core.exceptions import GoogleAPICallError
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gcp-verifier")

def verify():
    project_id = os.getenv("GCP_PROJECT_ID")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    print(f"--- Configuration ---")
    print(f"Project ID: {project_id}")
    print(f"Creds Path: {creds_path}")
    
    if not os.path.exists(creds_path):
        print(f"ERROR: Credentials file not found at {creds_path}")
        return

    try:
        print(f"--- Initializing Vertex AI ---")
        vertexai.init(project=project_id, location="us-central1")
        
        models_to_try = [
            "gemini-2.0-flash-exp", # Trying a known new one closer to user's guess if they meant 2.0
            "gemini-2.5-flash-lite-preview-09-2025", # User's specific request
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "gemini-pro"
        ]
        
        for model_name in models_to_try:
            print(f"--- Testing Model: {model_name} ---")
            try:
                model = GenerativeModel(model_name)
                response = model.generate_content("Hello, are you active?")
                print(f"--- SUCCESS with {model_name} ---")
                print(f"Response: {response.text}")
                return # Exit on first success
            except Exception as e:
                print(f"Failed with {model_name}: {e}")
                
    except Exception as e:
        print(f"--- GOOGLE API ERROR ---")
        print(f"Code: {e.code}")
        print(f"Message: {e.message}")
        print(f"Details: {e.errors}")
    except Exception as e:
        print(f"--- UNEXPECTED ERROR ---")
        print(e)

if __name__ == "__main__":
    verify()
