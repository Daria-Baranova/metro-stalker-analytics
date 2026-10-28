"""Ручна перевірка VADER: вибірка коментарів для розмітки і збереження міток у seed."""
import csv
import sys
from pathlib import Path

from ingest.common import postgres_connection

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "labeling" / "vader_sample.csv"
SEED = ROOT / "dbt" / "seeds" / "vader_labels.csv"
TARGET = 100
LABELS = {"+": "positive", "-": "negative", "0": "neutral"}
QUERY = "select comment_id, comment_text from silver.stg_comments order by md5(comment_id) limit 200"


def make_sheet():
    if SHEET.exists():
        sys.exit(f"{SHEET} вже існує — не перезаписую розмітку")
    connection = postgres_connection()
    with connection, connection.cursor() as cursor:
        cursor.execute(QUERY)
        rows = cursor.fetchall()
    connection.close()

    SHEET.parent.mkdir(exist_ok=True)
    with open(SHEET, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["human_label", "comment_text", "comment_id"])
        for comment_id, text in rows:
            writer.writerow(["", " ".join((text or "").split()), comment_id])
    print(f"Записано {len(rows)} коментарів у {SHEET}")


def save_seed():
    with open(SHEET, encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    unknown = {row["human_label"].strip() for row in rows} - set(LABELS) - {"", "x"}
    if unknown:
        sys.exit(f"Невідомі мітки: {unknown} — дозволено + - 0 x")
    labeled = [row for row in rows if row["human_label"].strip() in LABELS]
    if len(labeled) < TARGET:
        sys.exit(f"Розмічено {len(labeled)} з {TARGET} — продовжуй розмітку")

    with open(SEED, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["comment_id", "human_label"])
        for row in labeled:
            writer.writerow([row["comment_id"], LABELS[row["human_label"].strip()]])
    print(f"Записано {len(labeled)} міток у {SEED}")


if __name__ == "__main__":
    {"sample": make_sheet, "save": save_seed}[sys.argv[1]]()