import logging
import uuid

import typer
from job_cd.core.interfaces import (
    CompanyExtractorStrategy,
    ContactFinderStrategy,
    JobIntakeStrategy,
    PipelineStep, EmailComposerStrategy, DatabaseStrategy
)
from job_cd.core.models import (
    JobDeployment,
    IntakePayload,
    DeploymentProfile,
    DeploymentStatus, Outreach, Company
)
from job_cd.utils import get_next_scheduled_time


class JobPipelineEngine:
    def __init__(self, intake_strategy: JobIntakeStrategy, pipeline_steps: list[PipelineStep], db: DatabaseStrategy = None):
        self.intake_strategy = intake_strategy
        self.pipeline_steps = pipeline_steps
        self.db = db

    def run(self, payload: IntakePayload, profile: DeploymentProfile) -> list[JobDeployment]:
        logging.info("Starting job pipeline engine...")
        jobs = self.intake_strategy.fetch_jobs(payload)

        if not jobs:
            logging.warning("No jobs found.")
            return []

        logging.info(f"Found {len(jobs)} jobs. Starting jobs build...")
        deployments = []
        for job in jobs:
            deployment = JobDeployment(
                id=str(uuid.uuid4()),
                job=job,
                profile=profile,
                company=None,
                status=DeploymentStatus.PENDING,
                payload=payload,
            )

            for step in self.pipeline_steps:
                typer.secho(f"⏳ Starting {step.__class__.__name__}...", fg=typer.colors.CYAN)

                deployment = step.process(deployment)
                self.db.save(deployment)
                typer.secho(step.process_message(deployment), fg=typer.colors.GREEN, bold=True)

                if deployment.status == DeploymentStatus.FAILED:
                    logging.error(f"Failed to process job {job.id} @ {step.__class__.__name__}")
                    break
            
            deployments.append(deployment)
        
        return deployments
    

class ExtractorStep(PipelineStep):
    """
    The Pipeline Step that manages the CompanyExtractorStrategy.
    It protects the pipeline by checking statuses and handling failures safely.
    """
    def __init__(self, extractor: CompanyExtractorStrategy):
        self.extractor = extractor

    def process(self, deployment: JobDeployment) -> JobDeployment:
        if deployment.status == DeploymentStatus.FAILED:
            return deployment

        logging.info(f"Extracting company details for Job: {deployment.job.id}")
        
        # Handle manual overrides
        if deployment.payload and deployment.payload.manual_title:
            deployment.job.title = deployment.payload.manual_title
        
        if deployment.payload and deployment.payload.manual_company and deployment.payload.manual_domain:
            # Create company manually with overrides
            company = Company(
                id=str(uuid.uuid4()),
                name=deployment.payload.manual_company,
                domain=deployment.payload.manual_domain,
                job_title=deployment.job.title
            )
            deployment.company = company
            deployment.status = DeploymentStatus.EXTRACTED
        else:
            # Call extractor for missing fields
            company = self.extractor.extract_company(deployment.job)
            
            # Check if company exists and has both domain and job_title
            if company and company.domain and company.job_title:
                # If manual title was provided, ensure it's used
                if deployment.payload and deployment.payload.manual_title:
                    company.job_title = deployment.job.title
                deployment.company = company
                deployment.status = DeploymentStatus.EXTRACTED
                deployment.job.title = company.job_title
            else:
                logging.error(f"🚨 ExtractorStep failed to parse title/domain for Job {deployment.job.id}.")
                deployment.status = DeploymentStatus.FAILED
            
        return deployment
    
    def process_message(self, deployment: JobDeployment) -> str:
        if deployment.status == DeploymentStatus.EXTRACTED:
            return f"🎉 Extracted company details for Job: {deployment.job.id}"
        elif deployment.status == DeploymentStatus.FAILED:
            return f"🚨 Unable to parse job title or domain for this job post. Please try again."
        else:
            return f"🛸 Extracting company details for Job: {deployment.job.id}"


class FinderStep(PipelineStep):

    def __init__(self, finder: ContactFinderStrategy):
        self.finder = finder

    def process(self, deployment: JobDeployment) -> JobDeployment:
        if deployment.status == DeploymentStatus.FAILED:
            return deployment

        if not deployment.company:
            deployment.status = DeploymentStatus.FAILED
            return deployment


        logging.info(f"Searching contact details for Job: {deployment.job.id}")
        contacts = self.finder.find_contacts(deployment.company, deployment.profile)

        if not contacts:
            deployment.status = DeploymentStatus.FAILED
            return deployment

        for contact in contacts:
            outreach = Outreach(contact=contact)
            deployment.outreaches.append(outreach)

        deployment.status = DeploymentStatus.CONTACTS_FOUND

        return deployment

    def process_message(self, deployment: JobDeployment) -> str:
        if deployment.status == DeploymentStatus.CONTACTS_FOUND:
            return f"🎯 Found {len(deployment.outreaches)} contacts for Job: {deployment.job.id}"
        elif deployment.status == DeploymentStatus.FAILED:
            return f"🚨 ContactFinderStep failed for Job {deployment.job.id}. Halting branch."
        else:
            return f"🔍 Searching contact details for Job: {deployment.job.id}"


class EmailComposerStep(PipelineStep):
    """
    Loops through all Outreach targets and uses the AI to draft
    a personalized email for each one.
    """
    def __init__(self, composer: EmailComposerStrategy):
        self.composer = composer

    def process(self, deployment: JobDeployment) -> JobDeployment:
        if deployment.status == DeploymentStatus.FAILED:
            return deployment

        if not deployment.outreaches:
            logging.warning(f"No outreach targets found for Job {deployment.job.id}. Skipping drafting phase.")
            return deployment

        successful_drafts = 0

        for outreach in deployment.outreaches:
            if outreach.draft:
                continue

            draft = self.composer.draft_email(
                job=deployment.job,
                company=deployment.company,
                contact=outreach.contact,
                profile=deployment.profile
            )

            if not draft:
                outreach.status = DeploymentStatus.FAILED
                continue

            outreach.draft = draft
            outreach.status = DeploymentStatus.DRAFTED

            outreach.scheduled_at = get_next_scheduled_time(
                time_str=deployment.profile.default_schedule_time,
                tz_string=deployment.profile.timezone
            )

            successful_drafts += 1

            # --- NEW: Print the generated draft to the terminal ---
            typer.secho(f"\n--- 📝 Draft for {outreach.contact.name} ---", fg=typer.colors.MAGENTA, bold=True)
            typer.secho(f"To: {draft.recipient_email}", fg=typer.colors.CYAN)
            typer.secho(f"Subject: {draft.subject}", fg=typer.colors.CYAN, bold=True)
            typer.secho("Body:", fg=typer.colors.CYAN)

            # Using standard echo for the body so it handles line breaks and HTML cleanly
            typer.echo(draft.body)

            typer.secho("-" * 45 + "\n", fg=typer.colors.MAGENTA)
            # ------------------------------------------------------

        if successful_drafts == len(deployment.outreaches):
            deployment.status = DeploymentStatus.DRAFTED
        elif successful_drafts == 0:
            deployment.status = DeploymentStatus.FAILED
        else:
            deployment.status = DeploymentStatus.PARTIALLY_DRAFTED

        return deployment



    def process_message(self, deployment: JobDeployment) -> str:
        draft_count = sum(1 for o in deployment.outreaches if o.draft)

        if draft_count > 0:
            return f"✍️  Successfully drafted {draft_count} personalized emails!"
        elif not deployment.outreaches:
            return f"⏭️  No contacts to email for Job {deployment.job.id}. Skipping drafting phase."
        else:
            return f"🚨 Drafter failed to generate any emails for Job {deployment.job.id}."