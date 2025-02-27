from setuptools import setup, find_packages

setup(
    name="job_tracker",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        # API and Database
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.23.2",
        "sqlalchemy>=2.0.23",
        "alembic>=1.12.1",
        "psycopg2-binary>=2.9.9",
        "pydantic>=2.4.2",
        "python-multipart>=0.0.6",
        
        # Web Scraping
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "aiohttp>=3.8.6",
        "lxml>=4.9.3",
        
        # Dashboard
        "streamlit>=1.28.2",
        "pandas>=2.1.3",
        "plotly>=5.18.0",
        "numpy>=1.26.2",
        
        # Scheduling
        "apscheduler>=3.10.4",
        "schedule>=1.2.1",
        
        # Utilities
        "python-dateutil>=2.8.2",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
        ],
    },
    python_requires=">=3.9",
)
