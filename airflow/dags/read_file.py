from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime
import re
import cohere
import os
from dotenv import load_dotenv

load_dotenv()

def clean_text(input_text):
    """
    Cleans the input text by removing unnecessary characters like pronunciation guides,
    inline references, footnotes, and extra spaces.
    """
    # Remove pronunciation guides (e.g., /ˈdɑːkə/)
    text = re.sub(r"/[^/]+?/", "", input_text)
    
    # Remove inline references and citations (e.g., [20], [21])
    text = re.sub(r"\[\d+\]", "", text)
    
    # Remove symbols like ⓘ
    text = re.sub(r"ⓘ", "", text)

    # Remove non-English characters
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    
    # Remove extra spaces, tabs, and newlines
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def clean_file(**kwargs):
    # Get the file path from the DAG's configuration
    file_path = kwargs["dag_run"].conf.get("file_path")
    print("Pinged from FastAPI /upload API")
    print(f"Filename: {file_path}")
    
    # Read and clean the contents of the file
    try:
        with open(file_path, "r") as file:
            content = file.read()

        # Clean the text
        cleaned_content = clean_text(content)
        print("Cleaned File Content:")
        print(cleaned_content)

        # Push the cleaned content and filename to XCom
        kwargs['ti'].xcom_push(key="cleaned_content", value=cleaned_content)
        kwargs['ti'].xcom_push(key="filename", value=file_path)
    except Exception as e:
        print(f"Error reading or cleaning file: {e}")

def summarize_text(**kwargs):
    # Retrieve the cleaned text from XCom
    cleaned_content = kwargs['ti'].xcom_pull(task_ids='clean_file_task', key="cleaned_content")
    file_path = kwargs['ti'].xcom_pull(task_ids='clean_file_task', key="filename")

    # Get only the filename
    filename = file_path.split("/")[-1]

    print(f"Filename: {filename}")
    if not cleaned_content:
        print("No cleaned content found. Skipping summarization.")
        return
    
    try:
        co = cohere.ClientV2(api_key=os.getenv("CO_API_KEY"))
        message = f"Summarize this text in five sentences:\n{cleaned_content}"

        response = co.chat(
            model="command-r-plus-08-2024", #https://docs.cohere.com/v2/docs/command-r-plus limit 20req/min
            messages=[{"role": "user", "content": message}]
        )

        summarized_content = response.message.content[0].text
        print("Summarized Content:")
        print(summarized_content)

        # Push the summary and filename to XCom
        kwargs['ti'].xcom_push(key="summarized_content", value=summarized_content)
        kwargs['ti'].xcom_push(key="filename", value=filename)
    except Exception as e:
        print(f"Error summarizing text: {e}")

default_args = {"start_date": datetime(2024, 12, 13)}
with DAG(
    dag_id="summarize_dag", 
    default_args=default_args, 
    schedule_interval=None,
    catchup=False) as dag:
    
    clean_file_task = PythonOperator(
        task_id="clean_file_task",
        python_callable=clean_file,
        provide_context=True,
    )
    
    summarize_task = PythonOperator(
        task_id="summarize_text_task",
        python_callable=summarize_text,
        provide_context=True,
    )

    #Using SQL parameters prevents SQL injection and automatically escapes special characters like apostrophes. 
    update_database_task = PostgresOperator(
        task_id="update_database_task",
        postgres_conn_id="postgres_localhost",
        sql="""
            INSERT INTO summary (filename, summary)
            VALUES (%(filename)s, %(summary)s)
            ON CONFLICT (filename)
            DO UPDATE SET summary = EXCLUDED.summary;
        """,
        parameters={
            "filename": "{{ ti.xcom_pull(task_ids='summarize_text_task', key='filename') }}",
            "summary": "{{ ti.xcom_pull(task_ids='summarize_text_task', key='summarized_content') }}"
        }
    )


    clean_file_task >> summarize_task >> update_database_task
