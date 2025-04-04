# Role Validation

This document describes the role validation feature added to the Job Tracker application to ensure that only relevant job roles are extracted from scraped data.

## Overview

The role validation system provides intelligent filtering of job roles to ensure that only roles relevant to the search criteria are included in the results. This helps eliminate noise and ensures that the job listings displayed to users are truly relevant to their search.

## Features

- **Normalize Role Names**: Standardizes role strings for consistent comparison
- **Validate Roles**: Checks if a role is valid based on input roles and known valid keywords
- **Filter Jobs**: Ensures only jobs with relevant roles are included in results
- **Extract Roles**: Extracts valid roles from job titles
- **Automatic Application**: Applied to all scrapers using a decorator

## How It Works

The role validation system works by:

1. Normalizing role names (lowercase, remove special characters, standardize spacing)
2. Checking if roles contain valid keywords (e.g., "data scientist", "engineer", "developer")
3. Comparing roles with the input search roles for similarity
4. Filtering out irrelevant roles (like "O9 Technical Architect" that don't match input criteria)

## Configuration

The system includes a comprehensive list of valid role keywords in the `VALID_ROLE_KEYWORDS` set. These include:

- Data Science & Analytics keywords
- Engineering & Development keywords
- Machine Learning & AI keywords
- Technical role keywords
- Management & Leadership keywords

You can extend this list by adding more keywords to the `VALID_ROLE_KEYWORDS` set in `app/scrapers/role_utils.py`.

## Testing

A testing utility is provided to verify the role validation functionality:

```bash
# Basic test
python test_role_validation.py

# Test with specific scraper
python test_role_validation.py --scraper salesforce

# Test with custom roles
python test_role_validation.py --roles "Data Scientist" "ML Engineer"

# Verbose output
python test_role_validation.py --verbose
```

## Examples

Here are some examples of how the validation works:

| Input Role            | Job Title                | Valid? | Reason                                     |
|-----------------------|--------------------------|--------|-------------------------------------------|
| "Data Scientist"      | "Senior Data Scientist"  | Yes    | Contains exact input role                  |
| "ML Engineer"         | "Machine Learning Eng."  | Yes    | Similar to input role                      |
| "AI Engineer"         | "Deep Learning Engineer" | Yes    | Contains valid keywords                    |
| "Software Developer"  | "Product Manager"        | No     | No overlap with input role                 |
| "Data Scientist"      | "O9 Technical Architect" | No     | Contains numbers, no valid keywords        |

## Implementation Details

The role validation is implemented in `app/scrapers/role_utils.py` and integrated into all scrapers via a decorator in `app/scrapers/__init__.py`.

Key functions:

- `normalize_role(role)`: Standardizes role strings
- `is_valid_role(role, input_roles)`: Checks if a role is valid
- `filter_roles(job_data, input_roles)`: Filters job data to only include valid roles
- `validate_job_roles(job, input_roles)`: Validates if a job has relevant roles
- `filter_jobs_by_role(jobs, input_roles)`: Filters a list of jobs by roles

The decorator `apply_role_filtering` wraps all scraper functions to automatically apply role validation to the results.

## Adding New Valid Roles

If you notice that certain valid roles are being filtered out, you can add them to the `VALID_ROLE_KEYWORDS` set in `app/scrapers/role_utils.py`.

Example:
```python
# Add new valid roles
VALID_ROLE_KEYWORDS.update([
    "new keyword",
    "another keyword",
])
```

## Troubleshooting

If you encounter issues with role validation:

1. Run the test utility with `--verbose` to see detailed validation results
2. Check the logs for messages about filtered roles
3. Update the `VALID_ROLE_KEYWORDS` set if needed
4. If necessary, modify the validation functions for specific edge cases
