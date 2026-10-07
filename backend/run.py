"""Datasphere Creator Backend Runner."""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print("==========================================================")
    print(f"Starting {settings.PROJECT_NAME} Backend (Phase 2)...")
    print(f"API available at: http://{settings.HOST}:{settings.PORT}")
    print("==========================================================")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
