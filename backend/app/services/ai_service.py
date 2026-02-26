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
    """Finds the root folder of the project."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

def init_gemini():
    """Initializes the Gemini 2.0 Flash model using service account credentials."""
    base_dir = get_base_dir()
    SERVICE_ACCOUNT_FILE = os.path.join(base_dir, 'secrets', 'vertex-ai-key.json')
    
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    with open(SERVICE_ACCOUNT_FILE) as f:
        project_id = json.load(f)['project_id']
        
    vertexai.init(project=project_id, location="us-central1", credentials=creds)
    return GenerativeModel("gemini-2.0-flash-001")

def get_menu_from_gcs():
    """Fetches the latest menu JSON from Google Cloud Storage."""
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
    """Retrieves the last 5 orders from the local SQLite database."""
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
        return "\n".join([f"Ordered: {o[0]} at {o[1]}" for o in orders]) if orders else "New user: No history."
    finally:
        conn.close()

# --- REINFORCEMENT LEARNING CONTEXT ---

def get_rl_user_context(user_id):
    """Aggregates weighted rewards (-2, 1, 3, 5) to determine user preferences."""
    base_dir = get_base_dir()
    db_path = os.path.join(base_dir, 'instance', 'breadandbutter.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # 🛡️ COALESCE ensures we get 0 instead of None if no data exists
        cursor.execute("""
            SELECT category, CAST(SUM(reward) AS REAL) as total_score
            FROM cloud_feedback 
            WHERE user_id = ? 
            GROUP BY category
        """, (user_id,))
        
        rows = cursor.fetchall()
        scores = {row[0]: row[1] for row in rows}
        
        # 🎯 Refined Logic for the AI:
        # A "Like" should ideally be an AddToCart (3) or Order (5)
        # We only send categories with score >= 3.0 as 'True Likes'
        likes = [cat for cat, score in scores.items() if score >= 3.0]
        
        # 🚫 Anything -2.0 or lower is a Hard Dislike
        dislikes = [cat for cat, score in scores.items() if score <= -2.0]
        
        return {
            "likes": likes, 
            "dislikes": dislikes, 
            "raw_scores": scores
        }
    finally:
        conn.close()

# --- MAIN RECOMMENDATION LOGIC ---

def get_recommendation_json(user_id):
    """The 'Brain' that combines RL data, Time, and Menu to generate picks."""
    model = init_gemini()
    raw_menu_json = get_menu_from_gcs()
    if not raw_menu_json:
        return json.dumps({"error": "Menu load failure"})

    # 1. Gather all contexts
    rl_data = get_rl_user_context(user_id)
    history = get_user_history_string(user_id)
    current_time_obj = datetime.now()
    current_time_str = current_time_obj.strftime("%I:%M %p")

    # 2. Clean Menu (Optimize for Token Usage)
    try:
        menu_data = json.loads(raw_menu_json)
        simplified_menu = []
        full_item_details = {} 
        
        for category_block in menu_data.get('menu_items', []):
            cat_name = category_block.get('category')
            for item in category_block.get('items', []):
                iid = str(item.get('item_id'))
                simplified_menu.append({
                    "id": iid,
                    "name": item.get('name'),
                    "price": item.get('price'),
                    "category": cat_name
                })
                # We store full details to fix any AI errors later
                full_item_details[iid] = {
                    "img": item.get('image_url', ''), 
                    "cat": cat_name
                }
        
        clean_menu_for_ai = json.dumps(simplified_menu)
    except Exception as e:
        return json.dumps({"error": f"Menu parsing error: {e}"})

    # 3. Build the Strategic Prompt
    prompt = f"""
    You are a Strategic Recommendation Engine for a food ordering app.
    Current Time: {current_time_str}
    User Recent History: {history}
    
    REINFORCEMENT LEARNING (RL) SCORES (Weighted):
    {rl_data['raw_scores']}
    
    NEVER RECOMMEND THESE CATEGORIES: {rl_data['dislikes']}

    MENU DATA:
    {clean_menu_for_ai}

    GOAL: Recommend 3 items.
    
    RULES:
    1. EXPLOITATION: Categories with scores >= 5.0 (like {rl_data['likes']}) indicate orders. Prioritize these.
    2. EXPLORATION: Include items from categories with scores 1.0 to 3.0 (Clicks/Carts).
    3. TIME-AWARE: Since it is {current_time_str}:
       - If Late Night (12AM-5AM): Prioritize light snacks/beverages like Green Tea over heavy meals.
       - If Meal Times: Prioritize the highest scoring categories.
    4. ABSOLUTE FILTER: Do not recommend anything from {rl_data['dislikes']}.

    RETURN ONLY THIS JSON FORMAT:
    {{
      "recommendations": [
        {{ "item_id": "string", "name": "string", "category": "string", "price": 0.0 }}
      ]
    }}
    """

    config = GenerationConfig(
        response_mime_type="application/json", 
        temperature=0.1, # Low temperature for logical consistency
        max_output_tokens=450
    )

    try:
        response = model.generate_content(prompt, generation_config=config)
        ai_output = json.loads(response.text)

        # 4. Post-Process: Data Validation
        for rec in ai_output.get('recommendations', []):
            iid = str(rec['item_id'])
            # Attach the real Image URL from GCS data
            rec['image_url'] = full_item_details.get(iid, {}).get('img', '')
            # Force the correct Category if the AI hallucinated or generalized
            if iid in full_item_details:
                rec['category'] = full_item_details[iid]['cat']

        return json.dumps(ai_output)

    except Exception as e:
        print(f"AI Generation Error: {e}")
        return json.dumps({"error": str(e)})