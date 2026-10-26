"""Експорт таблиці рішень з prod у results/decision_table.csv."""
import csv
from pathlib import Path

import psycopg2

from ingest.common import postgres_credentials

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "decision_table.csv"
QUERY = "select * from marts.mart_decision order by priority, lift desc"


def main():
    creds = postgres_credentials()
    connection = psycopg2.connect(
        host=creds["host"],
        port=creds["port"],
        dbname=creds["database"],
        user=creds["username"],
        password=creds["password"],
    )
    with connection, connection.cursor() as cursor:
        cursor.execute(QUERY)
        header = [column.name for column in cursor.description]
        rows = cursor.fetchall()
    connection.close()

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Записано {len(rows)} рядків у {OUTPUT}")


if __name__ == "__main__":
    main()