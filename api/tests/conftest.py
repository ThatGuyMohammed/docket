import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://docket:docket@localhost:5432/docket_test")
os.environ.setdefault("WEBHOOK_SECRET", "test-secret")
