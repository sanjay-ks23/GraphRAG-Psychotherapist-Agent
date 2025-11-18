from graph_rag.celery import celery_app
import time

@celery_app.task
def process_data_ingestion(data: dict):
    """
    A sample background task for data ingestion.
    """
    print(f"Starting data ingestion for: {data}")
    # Simulate a long-running process
    time.sleep(10)
    print("Data ingestion complete.")
    return {"status": "complete", "ingested_data": data}
