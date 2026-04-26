# Contributing to Job-CD

First off, thank you for considering contributing to `job-cd`! It's people like you that make it a great tool for everyone.

## 🏗️ Development Setup

1.  **Fork and Clone:**
    ```bash
    git clone https://github.com/yourusername/job-cd.git
    cd job-cd
    ```

2.  **Environment:**
    We recommend using Python 3.12 or higher.
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"  # Note: Add dev dependencies if needed
    ```

3.  **Configuration:**
    Copy `.env.example` (if it exists) to `.env` and fill in your API keys.

## 🛠️ Project Structure

- `job_cd/main.py`: The CLI entry point using Typer.
- `job_cd/core/`: The "Engine Room."
    - `interfaces.py`: Abstract Base Classes (Strategies).
    - `pipeline.py`: The `JobPipelineEngine` and step logic.
    - `models.py`: Pydantic data models.
- `job_cd/providers/`: Concrete implementations of strategies (e.g., `ApolloFinder`, `GeminiExtractor`).
- `job_cd/enums.py`: Centralized status and type enums, including `DeploymentStatus`.

## 🧩 Extending the System

`job-cd` is built to be "Interface-First." You can extend it in two ways:

### 1. Adding a New Provider (Concrete Implementation)
If you want to use a different service (e.g., swapping Apollo for Hunter.io):
1.  **Identify the Interface:** Check `job_cd/core/interfaces.py` for the relevant abstract class (e.g., `ContactFinderStrategy`).
2.  **Implement:** Create your concrete class in `job_cd/providers/`.
3.  **Inject:** In `job_cd/main.py`, swap the default provider with your new implementation.

### 2. Adding a New Pipeline Step (New Logic)
If you want to add an entirely new stage to the process (e.g., a "Company Research" step):
1.  **Define a New Strategy Interface:** In `job_cd/core/interfaces.py`, define an `ABC` for your new logic.
2.  **Define a Pipeline Step Wrapper:** In `job_cd/core/pipeline.py`, create a new `PipelineStep` implementation.
3.  **Manage State:** Your step must update `deployment.status` using the `DeploymentStatus` enum (e.g., transitioning from `EXTRACTED` to a new state).
4.  **Register the Step:** Add your new step to the `pipeline_steps` list in `job_cd/main.py`.

```python
# Example of adding a new step in main.py
engine = JobPipelineEngine(
    intake_strategy=intake,
    pipeline_steps = [
        ExtractorStep(extractor=extractor),
        MyNewCustomStep(provider=custom_provider), # Your new step here
        FinderStep(finder=finder),
        # ...
    ],
    db=db,
)
```

## 📏 Coding Standards

- **Type Hints:** All new code must use Python type hints.
- **Pydantic:** Use Pydantic models for all data structures.
- **Async (Optional):** Currently the project is synchronous for simplicity, but we are open to moving to `httpx` and `asyncio` for network-bound tasks.
- **Linting:** We follow PEP 8. Please run `flake8` or `black` before submitting.

## 🧪 Testing

We are in the process of building out our test suite. If you add a feature, please include a test case in a new `tests/` directory.

## 📬 Pull Request Process

1.  Create a new branch for your feature or bugfix.
2.  Write clear, concise commit messages.
3.  Ensure your code doesn't break existing functionality.
4.  Update the documentation if you've added or changed any CLI commands.
5.  Submit your PR and wait for review!

## 📜 License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
