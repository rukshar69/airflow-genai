from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
# import cohere

def summarize_file(**kwargs):
    print('Pinged from FastAPI /upload API')
    # file_path = kwargs["dag_run"].conf.get("file_path")
    # with open(file_path, "r") as f:
    #     text = f.read()

    # Use Co:here API for summarization
    # co = cohere.Client("your-cohere-api-key")
    # response = co.summarize(text=text)
    # summary = response.summary

    # Save the summary
    # with open(f"{file_path}.summary.txt", "w") as f:
    #     f.write(summary)

default_args = {"start_date": datetime(2024, 12, 13)}
with DAG(
         dag_id="summarize_dag", 
         default_args=default_args, 
         schedule_interval=None,
         catchup=False) as dag:
    summarize_task = PythonOperator(
        task_id="summarize_file",
        python_callable=summarize_file,
        provide_context=True,
    )
