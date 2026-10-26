import os

import dlt
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