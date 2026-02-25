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

    # Initialize Vertex AI with the specific region
    vertexai.init(project=project_id, location="us-central1", credentials=creds)
    
    # FIX: Using 'gemini-1.5-flash-002' - Stable version, avoids 404 errors
    return GenerativeModel("gemini-2.0-flash-001")

# 2. Fetch Menu from Google Cloud Storage
def get_menu_from_gcs():
    base_dir = get_base_dir()
    SERVICE_ACCOUNT_FILE = os.path.join(base_dir, 'secrets', 'vertex-ai-key.json')
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    
    with open(SERVICE_ACCOUNT_FILE) as f:
        project_id = json.load(f)['project_id']

    storage_client = storage.Client(project=project_id, credentials=creds)
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
    model = init_gemini()
    raw_menu_json = get_menu_from_gcs()
    
    if not raw_menu_json:
        return json.dumps({"error": "Failed to load menu from Cloud Storage"})

    # --- 🛡️ TOKEN SAVER: Minimize Menu Data ---
    # We strip image URLs and long descriptions before sending to Gemini.
    # This prevents the "Token Exceeded" error and saves processing time.
    try:
        menu_data = json.loads(raw_menu_json)
        simplified_menu = []
        for category in menu_data.get('menu_items', []):
            for item in category.get('items', []):
                simplified_menu.append({
                    "id": item.get('item_id'),
                    "name": item.get('name'),
                    "price": item.get('price'),
                    "tags": item.get('tags', []),
                    "category": category.get('category')
                })
        clean_menu_for_ai = json.dumps(simplified_menu)
    except Exception:
        clean_menu_for_ai = raw_menu_json # Fallback

    history = get_user_history_string(user_id)
    current_time = datetime.now().strftime("%I:%M %p")
    
    # Configured for efficiency and stability
    config = GenerationConfig(
        response_mime_type="application/json",
        temperature=0.1,       # Lower temp = more relevant, less "hallucination"
        max_output_tokens=300  # Strict limit to save tokens
    )

    prompt = f"""
    You are a recommendation engine. 
    
    USER CONTEXT:
    - History: {history}
    
    MENU:
    {clean_menu_for_ai}

    TASK:
    Select 3 item_ids from the MENU that match the user's taste.
    Return ONLY a JSON object with this structure:
    {{
      "recommendations": [
        {{ 
          "item_id": "string", 
          "name": "string", 
          "price": 0.00
        }}
      ]
    }}
    """

    try:
        response = model.generate_content(prompt, generation_config=config)
        ai_output = json.loads(response.text)

        full_menu = json.loads(raw_menu_json)
        item_map = {}
        for cat in full_menu.get('menu_items', []):
            for itm in cat.get('items', []):
                item_map[str(itm['item_id'])] = itm.get('image_url', '')

        for rec in ai_output.get('recommendations', []):
            rec['image_url'] = item_map.get(str(rec['item_id']), '')
            # Ensure "reason" is removed if the AI added it anyway
            rec.pop('reason', None) 

        return json.dumps(ai_output)

    except Exception as e:
        print(f"AI Generation Error: {e}")
        return json.dumps({"error": str(e)})