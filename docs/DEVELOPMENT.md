# Development Guide

This guide covers key information for developers working on the Job Tracker project.

## Setting Up Development Environment

1. Clone the repository
```bash
git clone https://github.com/yourusername/job-tracker.git
cd job-tracker
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure Git hooks (optional but recommended)
```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit  # On Unix/Linux/macOS
```

## Testing

### Running Tests Locally

To run the basic tests:

```bash
# On Linux/macOS
bash scripts/run_tests.sh

# On Windows
powershell -File scripts/run_tests.ps1

# Or directly with pytest
pytest tests/test_basic.py -v
```

The pre-commit hook will automatically run these tests before each commit if you've configured git hooks as described above.

## Adding New Scrapers

To add a new company scraper:

1. Create a new file in `app/scrapers/` (e.g., `amazon.py`)
2. Implement the scraper function:

```python
def get_amazon_jobs(roles, days=7):
    """Scrape Amazon jobs for the given roles and time period"""
    # Implementation here
    return {
        "role1": [job1, job2, ...],
        "role2": [job3, job4, ...]
    }
```

3. Update `app/scheduler/jobs.py` to include your new scraper.

## Code Style

We follow these coding standards:

- PEP 8 for Python code style
- Docstrings for all functions and classes
- Type hints where appropriate
- Comprehensive error handling

## Database Migrations

If you make changes to database models, you need to create a migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

To apply migrations:

```bash
alembic upgrade head
```

## Deployment Process

When you push changes to the main branch, GitHub Actions will automatically:

1. Run tests
2. Deploy to Oracle Cloud if tests pass

You can also deploy manually:

```bash
ssh <your-server> "cd ~/job-tracker && git pull && bash scripts/deploy.sh"
```

## Troubleshooting

### Common Development Issues

1. **Database connection errors**: Check that your PostgreSQL server is running and your `.env` file has the correct connection string.

2. **Import errors**: Ensure you're running commands from the project root directory and your virtual environment is activated.

3. **Test failures**: Run tests with `-v` flag for more detailed output to identify the issue.
