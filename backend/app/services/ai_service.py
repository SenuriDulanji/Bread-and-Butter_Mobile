import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.oauth2 import service_account
from google.cloud import storage
import sqlite3
import json
import os
from datetime import datetime

# Helper to find the project root folder
def get_base_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

# 1. Initialize Vertex AI
def init_gemini():
    base_dir = get_base_dir()
    SERVICE_ACCOUNT_FILE = os.path.join(base_dir, 'secrets', 'vertex-ai-key.json')
    
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    with open(SERVICE_ACCOUNT_FILE) as f:
        project_id = json.load(f)['project_id']

    vertexai.init(project=project_id, location="us-central1", credentials=creds)
    # Using the latest Gemini 2.0 Flash model
    return GenerativeModel("gemini-2.0-flash-exp")

# 2. Fetch Menu from Google Cloud Storage
def get_menu_from_gcs():
    base_dir = get_base_dir()
    SERVICE_ACCOUNT_FILE = os.path.join(base_dir, 'secrets', 'vertex-ai-key.json')
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    
    with open(SERVICE_ACCOUNT_FILE) as f:
        project_id = json.load(f)['project_id']

    # Initialize GCS Client
    storage_client = storage.Client(project=project_id, credentials=creds)
    
    # --- IMPORTANT: Ensure these match your Cloud Console exactly ---
    BUCKET_NAME = "foodmenu_item" 
    FILE_NAME = "menu_items.json"
    
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(FILE_NAME)
        return blob.download_as_text()
    except Exception as e:
        print(f"Error fetching from GCS: {e}")
        return None

# 3. Fetch User History from local SQLite
def get_user_history_string(user_id):
    base_dir = get_base_dir()
    db_path = os.path.join(base_dir, 'instance', 'breadandbutter.db')
    
    # Connect and use double-quotes for the reserved "order" table name
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT items, created_at 
            FROM "order" 
            WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT 5
        """, (user_id,))
        
        orders = cursor.fetchall()
        if not orders:
            return "New user: No order history yet."
        
        return "\n".join([f"Ordered: {o[0]} at {o[1]}" for o in orders])
        
    except sqlite3.OperationalError as e:
        return f"Database error: {e}"
    finally:
        conn.close()

# 4. Main Recommendation Logic
def get_recommendation_json(user_id):
    # Initialize components
    model = init_gemini()
    menu_json = get_menu_from_gcs()
    
    if not menu_json:
        return json.dumps({"error": "Failed to load menu from Cloud Storage"})

    history = get_user_history_string(user_id)
    current_time = datetime.now().strftime("%I:%M %p")
    
    # Set model to return strictly structured JSON
    config = GenerationConfig(
        response_mime_type="application/json",
        temperature=0.7 # Adds a little creativity to the reasoning
    )

    prompt = f"""
    You are the AI recommendation engine for the 'Bread & Butter' food app.
    
    USER CONTEXT:
    - Current Time: {current_time}
    - Recent Orders: {history}
    
    MENU CATALOG (JSON):
    {menu_json}

    TASK:
    1. Analyze the user's history to identify flavor preferences (e.g., spicy, vegetarian, heavy/light).
    2. Select 3 specific items from the provided Menu Catalog.
    3. Ensure recommendations fit the time of day ({current_time}).
    4. Use the 'tags' and 'spiciness' fields in the menu for better matching.

    OUTPUT FORMAT:
    Return ONLY a JSON object with this structure:
    {{
      "recommendations": [
        {{ 
          "item_id": "string", 
          "name": "string", 
          "reason": "Explain why this matches their history or the current time",
          "image_url": "string",
          "price": 0.00
        }}
      ]
    }}
    """

    response = model.generate_content(prompt, generation_config=config)
    return response.text