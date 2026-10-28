import os

import dlt
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def postgres_credentials():
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5433")),
        "database": os.environ["POSTGRES_DB"],
        "username": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
    }


def postgres_destination():
    return dlt.destinations.postgres(credentials=postgres_credentials())

FREEZE_CONTRACT = {"tables": "evolve", "columns": "freeze", "data_type": "freeze"}

def postgres_connection():
    creds = postgres_credentials()
    return psycopg2.connect(
        host=creds["host"],
        port=creds["port"],
        dbname=creds["database"],
        user=creds["username"],
        password=creds["password"],
    )