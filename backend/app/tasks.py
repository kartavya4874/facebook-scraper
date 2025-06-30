from celery import Celery
from decouple import config
from .scraper import run_scraping_job

# Celery configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

celery_app = Celery(
    'facebook_scraper',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'app.tasks.scrape_facebook_group': {'queue': 'scraping'},
    }
)

@celery_app.task(name='app.tasks.scrape_facebook_group')
def scrape_facebook_group(job_id: int):
    """Celery task to scrape Facebook group"""
    try:
        run_scraping_job(job_id)
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        return {"status": "error", "job_id": job_id, "error": str(e)}

