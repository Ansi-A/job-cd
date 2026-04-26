from typing import List
from job_cd.enums import DeploymentStatus
import logging
import uuid
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from job_cd.core.interfaces import JobIntakeStrategy
from job_cd.core.models import Job, IntakePayload

class SimpleWebIntake(JobIntakeStrategy):
    """
    A lightweight scraper that takes any job URL, downloads the page, 
    and strips the HTML to get the raw text.
    """
    def fetch_jobs(self, payload: IntakePayload) -> List[Job]:
        if not payload.url:
            raise ValueError("SimpleWebIntake requires a 'url' in the payload.")

        url_str = str(payload.url)
        logging.info(f"Fetching job data from {url_str}")

        try:
            # 1. Fetch the raw page html
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url_str, headers=headers, timeout=10)
            response.raise_for_status()

            # 2. Extract clean text
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(['script', 'style']):
                script.extract()

            clean_text = soup.get_text(separator=" ", strip=True)

            # 3. Build the job object            
            job = Job(
                id=str(uuid.uuid4()),
                source="web",
                job_url=url_str,
                status=DeploymentStatus.PENDING,
                job_description=clean_text[:5000],
                created_at=datetime.now(timezone.utc),
            )

            return [job]

        except Exception as e:
            logging.error(f"Failed to scrape URL {url_str}: {e}")
            return []
        