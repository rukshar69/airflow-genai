from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
from contextlib import asynccontextmanager
import os
from fastapi.middleware.cors import CORSMiddleware
#uvicorn app:app --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the folder where files will be saved
UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_file_upload(upload_dir: Path = UPLOAD_DIR):
    """Dependency to validate and ensure upload directory exists."""
    if not upload_dir.is_dir():
        raise HTTPException(status_code=500, detail="Upload directory is not configured correctly.")
    return upload_dir

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...), upload_dir: Path = Depends(validate_file_upload)
):
    """Handles file uploads and saves them to the designated folder."""
    try:
        # Save file to the upload directory
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"message": "File uploaded successfully", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Optional health check endpoint
@app.get("/health")
async def health_check():
    """Simple endpoint to verify the API is running."""
    return {"status": "ok"}
