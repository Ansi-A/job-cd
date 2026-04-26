import logging
from datetime import timezone, datetime
from typing import Tuple, Callable, List

from job_cd.core.interfaces import DatabaseStrategy, EmailSenderStrategy
from job_cd.core.models import Outreach, JobDeployment
from job_cd.enums import DeploymentStatus


class Dispatcher:
    """
    Handles the Continuous Delivery side of the application.
    Checks the database queue and dispatches emails that are due.
    """
    def __init__(self, db: DatabaseStrategy, sender: EmailSenderStrategy):
        self.db = db
        self.sender = sender

    def dispatch_due_email(self, force: bool = False) -> Tuple[int, int]:
        queue = self.db.filter(
            status=DeploymentStatus.DRAFTED,
            scheduled_only=True,
            order_by="scheduled_at ASC",
            limit=3000
        )

        now_utc = datetime.now(timezone.utc)

        def is_due(outreach: Outreach) -> bool:
            if outreach.status != DeploymentStatus.DRAFTED:
                return False
            return force or now_utc >= outreach.scheduled_at

        return self._process_queue(queue, is_due, "Dispatching")

    def retry_failed_email(self) -> Tuple[int, int]:
        queue = (self.db.filter(status=DeploymentStatus.FAILED, limit=1000) +
                 self.db.filter(status=DeploymentStatus.PARTIALLY_SENT, limit=1000))

        def is_failed(outreach: Outreach) -> bool:
            return outreach.status == DeploymentStatus.FAILED

        return self._process_queue(queue, is_failed, "♻️ Retrying")



    def _process_queue(self, queue: List[JobDeployment], condition: Callable[[Outreach], bool], log_prefix: str) -> Tuple[int, int]:
        """
        Iterates through a given queue and processes outreaches
        that pass the provided condition function. Ensures immediate database persistence.
        """
        sent_count = 0
        failed_count = 0

        for deployment in queue:
            modified = False

            for outreach in deployment.outreaches:
                if condition(outreach):
                    logging.info(f"{log_prefix} email to {outreach.contact.name}...")

                    if self._attempt_send(outreach):
                        sent_count += 1
                    else:
                        failed_count += 1

                    self.db.save(deployment)
                    modified = True

            # After all outreaches for this job are done, evaluate and save the parent status
            if modified:
                self._sync_root_status(deployment)

        return sent_count, failed_count

    def _attempt_send(self, outreach: Outreach) -> bool:
        """
        Executes the SMTP payload .
        """
        try:
            success = self.sender.send_email(outreach.draft)
            if success:
                outreach.status = DeploymentStatus.SENT
                outreach.sent_at = datetime.now(timezone.utc)
            else:
                outreach.status = DeploymentStatus.FAILED
            return success

        except Exception as e:
            logging.error(f"Failure while sending to {outreach.contact.name}: {e}")
            outreach.status = DeploymentStatus.FAILED
            return False

    def _sync_root_status(self, deployment: JobDeployment) -> None:
        """
        Evaluates child statuses, updates the parent model, and saves it.
        """
        if all(o.status == DeploymentStatus.SENT for o in deployment.outreaches):
            deployment.status = DeploymentStatus.SENT
        else:
            deployment.status = DeploymentStatus.PARTIALLY_SENT

        self.db.save(deployment)