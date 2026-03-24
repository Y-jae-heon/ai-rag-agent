from dotenv import load_dotenv
import os

load_dotenv()

RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://localhost:8000")
