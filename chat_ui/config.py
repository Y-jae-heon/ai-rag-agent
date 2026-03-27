from dotenv import load_dotenv
import os
from langsmith import configure


load_dotenv()

RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://localhost:8000")

print("langsmith 추적 여부: ", os.getenv("LANGCHAIN_TRACING_V2"))
configure(project_name=os.getenv("LANGCHAIN_PROJECT") or "test-env")