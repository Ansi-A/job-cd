from abc import ABC, abstractmethod
from typing import List, Optional

from job_cd.core.models import (
    IntakePayload,
    Job, 
    Company, 
    Contact, 
    DeploymentProfile, 
    JobDeployment,
    EmailDraft
)
from job_cd.enums import DeploymentStatus


# --- THE DATABASE CONTRACT ---
class DatabaseStrategy(ABC):
    """
    Handles persistent storage of job deployments.
    """
    @abstractmethod
    def save(self, deployment: JobDeployment) -> None:
        """Saves or overwrites the current state of the deployment."""
        pass

    @abstractmethod
    def get(self, deployment_id: str) -> Optional[JobDeployment]:
        """Retrieves a deployment by ID."""
        pass

    def filter(self,
               status: Optional[DeploymentStatus] = None,
               scheduled_only: bool = False,
               job_link: Optional[str] = None,
               limit: int = 500,
               order_by: str = "rowid DESC") -> List[JobDeployment]:
        """
        Retrieves a list of deployments matching the given criteria.
        """
        pass

    @abstractmethod
    def update_status(self, deployment_id: str, new_status: DeploymentStatus) -> bool:
        """Updates only the status of a specific deployment."""
        pass


# --- THE PIPELINE CONTRACT ---
class PipelineStep(ABC):
    """
    Receives a JobDeployment and returns a JobDeployment after 
    processing the state in the current step.
    """
    @abstractmethod
    def process(self, deployment: JobDeployment) -> JobDeployment:
        pass
    
    @abstractmethod
    def process_message(self, deployment: JobDeployment) -> str:
        pass


# --- THE STRATEGY CONTRACTS ---
class JobIntakeStrategy(ABC):
    @abstractmethod
    def fetch_jobs(self, payload: IntakePayload) -> List[Job]:
        pass

class CompanyExtractorStrategy(ABC):
    @abstractmethod
    def extract_company(self, job: Job) -> Optional[Company]:
        pass

class ContactFinderStrategy(ABC):
    @abstractmethod
    def find_contacts(self, company: Company, profile: DeploymentProfile) -> List[Contact]:
        pass

class EmailComposerStrategy(ABC):
    @abstractmethod
    def draft_email(self, job: Job, company: Company, contact: Contact, profile: DeploymentProfile) -> Optional[EmailDraft]:
        pass

class EmailSenderStrategy(ABC):
    @abstractmethod
    def send_email(self, draft: EmailDraft) -> bool:
        pass

class PersistenceStrategy(ABC):
    @abstractmethod
    def save(self, deployment: JobDeployment) -> None:
        pass

# --- CACHE CONTRACT ---
class CacheStrategy(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[any]:
        pass

    @abstractmethod
    def set(self, key: str, value: dict) -> None:
        pass