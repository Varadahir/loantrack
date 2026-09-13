import os
import socket
import time
from contextlib import asynccontextmanager
from decimal import Decimal

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "loantrack")
DB_USER = os.getenv("DB_USER", "loantrack")
DB_PASSWORD = os.getenv("DB_PASSWORD", "loantrack")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    open=False,
)


class LoanCreate(BaseModel):
    borrower_name: str = Field(min_length=1)
    loan_amount: Decimal = Field(gt=0)
    property_city: str | None = None
    status: str = "PENDING"


def wait_for_database(max_retries: int = 10, delay_seconds: int = 2) -> None:
    """Wait for PostgreSQL to become available before starting the API."""

    for attempt in range(1, max_retries + 1):
        try:
            with psycopg.connect(DATABASE_URL) as connection:
                connection.execute("SELECT 1")

            print(f"Database connection successful on attempt {attempt}.")
            return

        except psycopg.OperationalError as error:
            print(
                f"Database connection attempt {attempt}/{max_retries} failed: "
                f"{error}"
            )

            if attempt == max_retries:
                raise RuntimeError(
                    "Database did not become available after retries."
                ) from error

            sleep_time = delay_seconds * attempt
            print(f"Retrying database connection in {sleep_time} seconds...")
            time.sleep(sleep_time)


def run_migrations() -> None:
    """Apply the database schema migration."""

    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "db",
        "migrations",
        "001_create_loans.sql",
    )

    with open(migration_path, "r", encoding="utf-8") as migration_file:
        migration_sql = migration_file.read()

    with pool.connection() as connection:
        connection.execute(migration_sql)
        connection.commit()

    print("Database migration applied successfully.")


def seed_database() -> None:
    """Insert initial loan records when the table is empty."""

    seed_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "db",
        "seed",
        "001_seed_loans.sql",
    )

    with pool.connection() as connection:
        existing_count = connection.execute(
            "SELECT COUNT(*) FROM loans"
        ).fetchone()[0]

        if existing_count == 0:
            with open(seed_path, "r", encoding="utf-8") as seed_file:
                seed_sql = seed_file.read()

            connection.execute(seed_sql)
            connection.commit()
            print("Database seed data inserted.")
        else:
            print(f"Database already contains {existing_count} loan(s).")


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_database()

    pool.open()

    run_migrations()
    seed_database()

    yield

    pool.close()


app = FastAPI(
    title="LoanTrack API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/healthz")
def healthz():
    """Process health check. Does not depend on the database."""
    return {
        "status": "ok",
        "service": "loantrack-api",
    }


@app.get("/readyz")
def readyz():
    """Readiness check. Verifies that PostgreSQL is reachable."""

    try:
        with pool.connection() as connection:
            connection.execute("SELECT 1")

        return {
            "status": "ready",
            "database": "reachable",
        }

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unreachable",
                "error": str(error),
            },
        )


@app.get("/loans")
def get_loans():
    """Return all loans."""

    try:
        with pool.connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                rows = cursor.execute(
                    """
                    SELECT
                        id,
                        borrower_name,
                        loan_amount,
                        property_city,
                        status,
                        created_at
                    FROM loans
                    ORDER BY id
                    """
                ).fetchall()

        loans = []

        for row in rows:
            row["loan_amount"] = float(row["loan_amount"])
            row["created_at"] = row["created_at"].isoformat()
            loans.append(row)

        return {
            "served_by": os.getenv("HOSTNAME", socket.gethostname()),
            "loans": loans,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve loans: {error}",
        )


@app.post("/loans", status_code=201)
def create_loan(loan: LoanCreate):
    """Create a new loan."""

    try:
        with pool.connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                row = cursor.execute(
                    """
                    INSERT INTO loans (
                        borrower_name,
                        loan_amount,
                        property_city,
                        status
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING
                        id,
                        borrower_name,
                        loan_amount,
                        property_city,
                        status,
                        created_at
                    """,
                    (
                        loan.borrower_name,
                        loan.loan_amount,
                        loan.property_city,
                        loan.status,
                    ),
                ).fetchone()

            connection.commit()

        row["loan_amount"] = float(row["loan_amount"])
        row["created_at"] = row["created_at"].isoformat()

        return {
            "served_by": os.getenv("HOSTNAME", socket.gethostname()),
            "loan": row,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to create loan: {error}",
        )
