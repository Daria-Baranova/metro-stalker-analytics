"""Запуск усього пайплайна по черзі з логом тривалості."""
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "logs" / "run_all.log"

DBT = str(Path(sys.executable).with_name("dbt"))
DBT_DIR = ROOT / "dbt"

load_dotenv(ROOT / ".env")
HAS_YOUTUBE_KEY = bool(os.getenv("YOUTUBE_API_KEY", "").strip())
YOUTUBE_STEPS = {"Коментарі YouTube", "VADER: настрій коментарів"}
YOUTUBE_EXCLUDE = [] if HAS_YOUTUBE_KEY else [
    "--exclude", "source:bronze.youtube_comments+", "source:bronze.comment_sentiment+",
]

STEPS = [
    ("Відгуки Steam", [sys.executable, "-m", "ingest.steam_reviews"], ROOT),
    ("Ціни Steam і курс НБУ", [sys.executable, "-m", "ingest.steam_appdetails"], ROOT),
    ("Коментарі YouTube", [sys.executable, "-m", "ingest.youtube_comments"], ROOT),
    ("VADER: настрій коментарів", [sys.executable, "-m", "analysis.vader"], ROOT),
    ("dbt: свіжість джерел", [DBT, "source", "freshness", "--target", "prod", *YOUTUBE_EXCLUDE], DBT_DIR),
    ("dbt: build prod", [DBT, "build", "--target", "prod", *YOUTUBE_EXCLUDE], DBT_DIR),
    ("Експорт decision_table.csv", [sys.executable, "-m", "analysis.export_decision_table"], ROOT),
    ("Superset: імпорт дашборду", [sys.executable, "superset/dashboard.py", "import"], ROOT),
]


def log(message):
    line = f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC | {message}"
    print(line)
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(line + "\n")


def main():
    total_start = time.perf_counter()
    for name, command, cwd in STEPS:
        if name in YOUTUBE_STEPS and not HAS_YOUTUBE_KEY:
            log(f"УВАГА: пропускаю «{name}» — немає YOUTUBE_API_KEY, вкладка 5 буде порожня")
            continue
        log(f"Старт: {name}")
        start = time.perf_counter()
        result = subprocess.run(command, cwd=cwd)
        minutes = (time.perf_counter() - start) / 60
        if result.returncode != 0:
            log(f"ПОМИЛКА: {name} після {minutes:.1f} хв — зупиняюсь")
            sys.exit(result.returncode)
        log(f"Готово: {name} — {minutes:.1f} хв")
    log(f"Усе готово за {(time.perf_counter() - total_start) / 60:.1f} хв")


if __name__ == "__main__":
    main()