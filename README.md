# Job-CD 🚀

**An Automated Outreach Engine for Job Applications.**

`job-cd` is a specialized automation tool focused on the most critical phase of the job search: **personalized email outreach to hiring managers and recruiters**. It treats your career search like a modern software pipeline: taking a job URL as "source code," processing it through various "build steps" (extraction, contact discovery, email drafting), and finally "deploying" (sending) hyper-personalized outreach.

By defining clear interfaces for every stage, `job-cd` allows you to automate high-volume outreach without sacrificing the quality and personalization of a manual application.

## ✨ Features

- **Modular & Extensible:** Built on an "Interface-First" architecture. Every component—from the lead finder to the AI model—is a pluggable strategy.
- **Profile Management:** Define your "Persona" (experience, target roles, current title) in a local cache to ensure every outreach is tailored to your unique background.
- **Automated Intake:** Fetches and parses raw data from job posting URLs.
- **AI-Driven Extraction:** Automatically identifies company context and role requirements from unstructured text.
- **Intelligent Discovery:** Locates specific recruitment and engineering contacts at target companies.
- **Hyper-Personalized Content:** Generates tailored, high-conversion cold emails based on your profile and the specific job requirements.
- **Audit & History:** Comprehensive tracking of every application, contact, and email status in a local database.

## 📚 Documentation

Detailed documentation is available in the following files:

- **[Architecture Overview](docs/ARCHITECTURE.md)**: A deep dive into the system design, interfaces, and pipeline engine.
- **[Service Providers](docs/PROVIDERS.md)**: Details on integrated third-party services and how to add your own.
- **[Contributing Guide](CONTRIBUTING.md)**: Instructions for developers on how to extend the system and add new providers.
- **[License](LICENSE)**: Legal information regarding the project's MIT license.

## 🔌 Default Providers & Extensibility

While `job-cd` is designed to be provider-agnostic, it comes with default implementations for the following services:

| Component | Interface | Default Provider | Purpose |
| :--- | :--- | :--- | :--- |
| **Intake** | `JobIntakeStrategy` | `SimpleWebIntake` | Fetches raw data from job URLs. |
| **Extraction** | `CompanyExtractorStrategy` | `GeminiCliExtractor` | Parses job text into structured data. |
| **Discovery** | `ContactFinderStrategy` | `ApolloFinder` | Finds relevant recruiter/manager emails. |
| **Composition** | `EmailComposerStrategy` | `GeminiCliEmailComposer` | Drafts the personalized email body. |
| **Dispatch** | `EmailSenderStrategy` | `SmtpEmailSender` | Sends the final emails to recipients. |
| **Persistence** | `DatabaseStrategy` | `SQLiteDatabaseAdapter` | Maintains persistent history and status. |
| **Caching** | `CacheStrategy` | `LocalCache` | Handles local JSON storage (Profiles/API). |

> **Note:** Every concrete implementation listed above can be replaced. The system is built so that you can create your own class for any interface (e.g., swapping one lead discovery service for another) and inject it into the pipeline without changing the core engine.

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- **[Gemini CLI](https://geminicli.com/docs/get-started/installation/):** By default, the project uses the Gemini CLI in headless mode for AI tasks. You **must** have it installed and authenticated (`gemini login`) to use the default `GeminiCliExtractor` and `GeminiCliEmailComposer` providers.
- **API Keys:** For your chosen Discovery provider (e.g., Apollo.io).
- **SMTP Credentials:** For email dispatch. (Note: For **Gmail**, you must enable **2FA** and use an **[App Password](https://myaccount.google.com/apppasswords)**).

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/job-cd.git
cd job-cd

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install the package
pip install -e .
```

### Configuration

Create a `.env` file in the root directory and fill in the credentials for your specific providers. See `.env.example` for the required keys for default implementations.

### Personalization (Profiles)

`job-cd` uses your profile to tailor outreach. Configure this by creating a `profiles.json` file inside the `.cache` directory. 

#### Example Profile
```json
{
  "default": {
    "first_name": "Ted",
    "last_name": "Lasso",
    "email": "ted.lasso@afcrichmond.com",
    "current_role": "Head Coach",
    "years_of_experience": 20,
    "target_contact_titles": ["Owner", "Director of Football", "General Manager"],
    "resume_url": "https://linkedin.com/in/tedlasso",
    "resume_text": "# TED LASSO\nHead Coach | AFC Richmond\n\n- Expert in team building and 'Believe' philosophy.\n- Led AFC Richmond to significant growth and cultural transformation.\n- Specialized in turning skeptics into believers."
  }
}
```

#### Field Definitions
- `first_name` / `last_name`: Used for email signatures and personalized introductions.
- `email`: Your professional email address (used in the "From" field).
- `current_role`: Your current job title. This helps the AI frame your experience relative to the target role.
- `years_of_experience`: Total years in the industry.
- `target_contact_titles`: A list of roles you want the system to find at the target company (e.g., "Engineering Manager").
- `resume_url`: (Optional) Link to your LinkedIn or portfolio.
- `resume_text`: **Critical.** The full text of your resume. This is the primary source the AI uses to find relevant "hooks" and match your skills to the job description.
- `default_hook`: (Optional) A custom opening line or specific value proposition that appears at the **top** of the email body.
- `default_ask`: (Optional) Your specific call to action (e.g., "Are you free for a brief chat next Tuesday?") which appears at the **end** of the email.

## 📖 Usage

### 1. Build a Deployment
```bash
jobcd build "https://www.linkedin.com/jobs/view/123456789/"
```

### 2. Preview Drafts
```bash
jobcd preview
```

### 3. Dispatch Emails
```bash
jobcd dispatch
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
