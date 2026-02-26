import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.oauth2 import service_account
from google.cloud import storage
import sqlite3
import json
import os
from datetime import datetime

# --- HELPER FUNCTIONS ---

def get_base_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

def init_gemini():
    base_dir = get_base_dir()
    SERVICE_ACCOUNT_FILE = os.path.join(base_dir, 'secrets', 'vertex-ai-key.json')
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    with open(SERVICE_ACCOUNT_FILE) as f:
        project_id = json.load(f)['project_id']
    vertexai.init(project=project_id, location="us-central1", credentials=creds)
    return GenerativeModel("gemini-2.0-flash-001")

def get_menu_from_gcs():
    base_dir = get_base_dir()
    SERVICE_ACCOUNT_FILE = os.path.join(base_dir, 'secrets', 'vertex-ai-key.json')
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    with open(SERVICE_ACCOUNT_FILE) as f:
        project_id = json.load(f)['project_id']
    storage_client = storage.Client(project=project_id, credentials=creds)
    try:
        bucket = storage_client.bucket("foodmenu_item")
        blob = bucket.blob("menu_items.json")
        return blob.download_as_text()
    except Exception as e:
        print(f"Error fetching from GCS: {e}")
        return None

def get_user_history_string(user_id):
    base_dir = get_base_dir()
    db_path = os.path.join(base_dir, 'instance', 'breadandbutter.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT items, created_at FROM "order" WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', (user_id,))
        orders = cursor.fetchall()
        return "\n".join([f"Ordered: {o[0]} at {o[1]}" for o in orders]) if orders else "New user: No history."
    finally:
        conn.close()

# --- REINFORCEMENT LEARNING CONTEXT ---

def get_rl_user_context(user_id):
    db_path = os.path.join(get_base_dir(), 'instance', 'breadandbutter.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT category, SUM(reward) FROM cloud_feedback WHERE user_id = ? GROUP BY category", (user_id,))
        rows = cursor.fetchall()
        likes = [row[0] for row in rows if row[1] >= 1.0]
        dislikes = [row[0] for row in rows if row[1] <= -1.0]
        return {"likes": likes, "dislikes": dislikes}
    finally:
        conn.close()

# --- MAIN LOGIC (THE BRAIN) ---

def get_recommendation_json(user_id):
    model = init_gemini()
    raw_menu_json = get_menu_from_gcs()
    if not raw_menu_json:
        return json.dumps({"error": "Menu load failure"})

    # 1. Fetch RL context and history
    rl_memory = get_rl_user_context(user_id)
    history = get_user_history_string(user_id)
    current_time = datetime.now().strftime("%I:%M %p")

    # 2. Clean and Simplify Menu for Token Safety
    try:
        menu_data = json.loads(raw_menu_json)
        simplified_menu = []
        full_item_details = {} # To map images/categories back later
        
        for cat in menu_data.get('menu_items', []):
            cat_name = cat.get('category')
            for item in cat.get('items', []):
                iid = str(item.get('item_id'))
                simplified_menu.append({
                    "id": iid,
                    "name": item.get('name'),
                    "price": item.get('price'),
                    "category": cat_name
                })
                full_item_details[iid] = {"img": item.get('image_url', ''), "cat": cat_name}
        
        clean_menu_for_ai = json.dumps(simplified_menu)
    except Exception as e:
        return json.dumps({"error": f"Menu parsing error: {e}"})

    # 3. Build Prompt with RL Instructions
    prompt = f"""
    You are a recommendation engine for a food app.
    Current Time: {current_time}
    User History: {history}
    
    RL PREFERENCES (Net Rewards):
    - Preferred Categories (Boost): {rl_memory['likes']}
    - Disliked Categories (NEVER RECOMMEND): {rl_memory['dislikes']}

    MENU:
    {clean_menu_for_ai}

    TASK:
    Select 3 items. 
    - If it's night ({current_time}), prioritize light snacks/beverages like your Green Tea.
    - Respect RL: Prioritize {rl_memory['likes']} and exclude {rl_memory['dislikes']}.
    
    RETURN ONLY JSON:
    {{
      "recommendations": [
        {{ "item_id": "string", "name": "string", "category": "string", "price": 0.0 }}
      ]
    }}
    """

    config = GenerationConfig(response_mime_type="application/json", temperature=0.2)

    try:
        response = model.generate_content(prompt, generation_config=config)
        ai_output = json.loads(response.text)

        # 4. Post-Process: Attach Images and fix categories
        for rec in ai_output.get('recommendations', []):
            iid = str(rec['item_id'])
            rec['image_url'] = full_item_details.get(iid, {}).get('img', '')
            # If AI missed the category, we fill it from our local map
            if rec.get('category') == 'General' or not rec.get('category'):
                rec['category'] = full_item_details.get(iid, {}).get('cat', 'General')

        return json.dumps(ai_output)

    except Exception as e:
        print(f"AI Error: {e}")
        return json.dumps({"error": str(e)})