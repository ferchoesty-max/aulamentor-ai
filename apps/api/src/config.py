import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'aulamentor-ai-demo').strip()
PORT = int(os.getenv('PORT', '8000'))
CORS_ORIGINS = [o.strip() for o in os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',') if o.strip()]
