import os

import dlt
from dotenv import load_dotenv

load_dotenv()


def postgres_destination():
    credentials = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),  # з хоста — localhost
        "port": int(os.getenv("POSTGRES_PORT", "5433")),  # назовні — 5433
        "database": os.environ["POSTGRES_DB"],
        "username": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
    }
    return dlt.destinations.postgres(credentials=credentials)