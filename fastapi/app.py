from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from pathlib import Path
import requests
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import hashlib
from requests.auth import HTTPBasicAuth
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = "postgresql+psycopg2://airflow:airflow@localhost:5432/airflow"
engine = create_engine(DATABASE_URL)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the folder where files will be saved
UPLOAD_DIR = Path("/media/rukshar/partition2/code/airflow-genai/fastapi/uploaded_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

AIRFLOW_TRIGGER_URL = "http://localhost:8080/api/v1/dags/summarize_dag/dagRuns"
AIRFLOW_USERNAME = "airflow"
AIRFLOW_PASSWORD = "airflow"

def generate_hash(input_str: str, length: int = 10) -> str:
    """Generates a hash string of the specified length."""
    return hashlib.sha256(input_str.encode()).hexdigest()[:length]

def get_current_time_formatted() -> str:
    """Returns the current time in 'YYYY-MM-DDTHH:MM:SSZ' format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"

def validate_file_upload(upload_dir: Path = UPLOAD_DIR):
    """Dependency to validate and ensure upload directory exists."""
    if not upload_dir.is_dir():
        raise HTTPException(status_code=500, detail="Upload directory is not configured correctly.")
    return upload_dir

def trigger_airflow_dag(filename: str, current_time: str):
    """Triggers the Airflow DAG with the specified parameters."""
    dag_run_id = generate_hash(filename + current_time)
    payload = {
        "dag_run_id": dag_run_id,
        "logical_date": current_time,
        "execution_date": current_time,
        "data_interval_start": current_time,
        "data_interval_end": current_time,
        "conf": {"file_path": f"{filename}"},
        "note": f"Triggered by upload of file {filename}",
    }

    response = requests.post(
        AIRFLOW_TRIGGER_URL,
        json=payload,
        auth=HTTPBasicAuth(AIRFLOW_USERNAME, AIRFLOW_PASSWORD),
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to trigger Airflow DAG: {response.text}",
        )

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...), upload_dir: Path = Depends(validate_file_upload)
):
    """Handles file uploads and triggers an Airflow DAG."""
    try:
        # Save file to the upload directory
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Trigger Airflow DAG
        current_time = get_current_time_formatted()
        docker_file_path = f"/opt/airflow/uploaded_files/{file.filename}"
        trigger_airflow_dag(docker_file_path, current_time)

        return {"message": "File uploaded and DAG triggered successfully", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/summaries/")
async def get_summaries():
    """Fetch summaries from the 'summary' table."""
    try:
        connection = engine.connect()
        metadata = MetaData(bind=engine)
        summary_table = Table("summary", metadata, autoload_with=engine)
        
        query = select([summary_table.c.filename, summary_table.c.summary])
        result = connection.execute(query).fetchall()
        connection.close()
        
        summaries = [{"filename": row.filename, "summary": row.summary} for row in result]
        return JSONResponse(content=summaries)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Endpoint to download a file."""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path=str(file_path), filename=filename, media_type="application/octet-stream")

# Optional health check endpoint
@app.get("/health")
async def health_check():
    """Simple endpoint to verify the API is running."""
    return {"status": "ok"}
