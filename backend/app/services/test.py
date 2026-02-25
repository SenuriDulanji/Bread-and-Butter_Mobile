from app.services.ai_service import get_recommendation_json

print("--- TESTING AI + CLOUD STORAGE ---")
# This now pulls Menu from GCS and History from SQLite automatically
result = get_recommendation_json(user_id=1) 
print(result)