import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    DATA_DIR = BASE_DIR / "data"
    TEMPLATES_DIR = BASE_DIR / "templates"
    OUTPUT_DIR = BASE_DIR / "output"
    
    GLM_API_KEY = os.getenv("GLM_API_KEY", "")
    GLM_API_BASE = os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4/")
    GLM_MODEL = os.getenv("GLM_MODEL", "glm-4")
    
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    
    CHROMA_PERSIST_DIR = BASE_DIR / "knowledge" / "chroma_db"
    
    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
