# Technical Documentation: Architecture & Components

`job-cd` is designed as a modular, decoupled system where each component communicates via strictly defined interfaces. This document provides a detailed breakdown of every major component and interface in the project.

---

## 🏗️ Core Engine Components

### 1. `JobPipelineEngine` (`core/pipeline.py`)
The orchestrator of the entire process. It accepts an `IntakePayload`, uses an `IntakeStrategy` to fetch raw data, and then executes a series of `PipelineStep` objects.
- **Responsibility**: State management, step sequencing, and error handling at the pipeline level.
- **Key Method**: `run(payload, profile)`

### 2. `Dispatcher` (`core/dispatcher.py`)
Handles the final "deployment" (sending) of drafted emails.
- **Responsibility**: Queries the database for emails marked as `DRAFTED` that are due for delivery, and uses an `EmailSenderStrategy` to dispatch them.
- **Logic**: Implements scheduling logic and retry mechanisms for failed attempts.

---

## 🔌 Core Interfaces (`core/interfaces.py`)

Every major functional block in `job-cd` is defined as an Abstract Base Class (ABC). This allows any developer to provide their own concrete implementation.

### `JobIntakeStrategy`
- **Purpose**: Fetches raw data from a source (e.g., LinkedIn, Indeed, or a company career page).
- **Method**: `fetch_jobs(payload: IntakePayload) -> List[Job]`

### `CompanyExtractorStrategy`
- **Purpose**: Uses AI or parsing logic to identify the company name and website from raw job descriptions.
- **Method**: `extract_company(job: Job) -> Optional[Company]`

### `ContactFinderStrategy`
- **Purpose**: Locates recruitment or hiring contacts at a target company.
- **Method**: `find_contacts(company: Company, profile: DeploymentProfile) -> List[Contact]`

### `EmailComposerStrategy`
- **Purpose**: Generates the personalized email content using the job details, company context, and the user's profile.
- **Method**: `draft_email(job, company, contact, profile) -> Optional[EmailDraft]`

### `EmailSenderStrategy`
- **Purpose**: Handles the actual network communication to send the email (e.g., SMTP, SendGrid, Resend).
- **Method**: `send_email(draft: EmailDraft) -> bool`

### `DatabaseStrategy`
- **Purpose**: Provides persistence for job deployments and outreach history.
- **Methods**: `save()`, `get()`, `filter()`, `update_status()`

### `CacheStrategy`
- **Purpose**: Simple key-value storage for transient data (like API responses or user profiles).
- **Methods**: `get()`, `set()`

---

## 🔄 Pipeline Steps (`core/pipeline.py`)

Pipeline steps are wrappers around strategies that allow them to participate in the `JobPipelineEngine`. Each step is responsible for updating the `JobDeployment` state.

- **`ExtractorStep`**: Invokes the `CompanyExtractorStrategy`.
- **`FinderStep`**: Invokes the `ContactFinderStrategy`.
- **`EmailComposerStep`**: Invokes the `EmailComposerStrategy`.

To add a new stage to the pipeline (e.g., "Company Research"), you define a new interface and a corresponding `PipelineStep`.

---

## 📄 Data Models (`core/models.py`)

We use **Pydantic** for all internal data structures to ensure type safety and validation.

- **`JobDeployment`**: The root object representing an application attempt.
- **`DeploymentProfile`**: The user's "Persona" (resume details, target titles).
- **`Job`**: Details about the role.
- **`Company`**: Details about the hiring organization.
- **`Contact`**: Specific individuals identified for outreach.
- **`EmailOutreach`**: Tracks the status and content of a single email sent to a contact.
- **`EmailDraft`**: The subject and body of the proposed outreach.

---

## 🛠️ Providers (`providers/`)

Providers are the concrete implementations of the interfaces listed above.
- `SQLiteDatabaseAdapter`: Implementation of `DatabaseStrategy`.
- `ApolloFinder`: Implementation of `ContactFinderStrategy` using the Apollo.io API.
- `GeminiExtractor`/`GeminiCliEmailComposer`: Implementations using Google's Gemini LLM.
- `SmtpEmailSender`: Implementation of `EmailSenderStrategy` using standard SMTP.
- `LocalCache`: File-based implementation of `CacheStrategy`.

---

## 🔄 Deployment Lifecycle (`DeploymentStatus`)

The `JobDeployment` state is managed via the `DeploymentStatus` enum. Each pipeline step is responsible for transitioning the deployment to the next logical state.

| Status | Description |
| :--- | :--- |
| `PENDING` | Initial state after intake, waiting for extraction. |
| `EXTRACTED` | Company and job details have been successfully parsed. |
| `CONTACTS_FOUND` | Relevant recruitment or hiring contacts have been identified. |
| `DRAFTED` | Outreach emails have been composed for all found contacts. |
| `PARTIALLY_DRAFTED` | Emails were composed for some, but not all, contacts. |
| `SENT` | All outreach emails have been successfully dispatched. |
| `PARTIALLY_SENT` | Some emails were sent, while others failed or are pending. |
| `FAILED` | A critical error occurred in a pipeline step, halting that deployment. |
