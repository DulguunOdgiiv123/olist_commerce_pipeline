import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load variables from .env into environment
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Build the connection string
# Format: postgresql+psycopg2://user:password@host:port/dbname
connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(connection_string)

# Try a simple query to prove the connection works
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM orders"))
    count = result.scalar()
    print(f"Connected successfully! Number of orders: {count}")
