import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL server
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='1901',
    host='localhost'
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Create a cursor
cursor = conn.cursor()

# Check if database exists
cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'job_tracker'")
exists = cursor.fetchone()

if not exists:
    print("Creating database 'job_tracker'...")
    cursor.execute("CREATE DATABASE job_tracker")
    print("Database created successfully!")
else:
    print("Database 'job_tracker' already exists.")

# Close the connection
cursor.close()
conn.close()
