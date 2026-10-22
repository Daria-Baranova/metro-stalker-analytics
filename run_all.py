"""Запуск усього пайплайна по черзі з логом тривалості."""
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "logs" / "run_all.log"

STEPS = [
    ("Відгуки Steam", [sys.executable, "-m", "ingest.steam_reviews"]),
    ("Ціни Steam і курс НБУ", [sys.executable, "-m", "ingest.steam_appdetails"]),
    ("Коментарі YouTube", [sys.executable, "-m", "ingest.youtube_comments"]),
]


def log(message):
    line = f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC | {message}"
    print(line)
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(line + "\n")


def main():
    total_start = time.perf_counter()
    for name, command in STEPS:
        log(f"Старт: {name}")
        start = time.perf_counter()
        result = subprocess.run(command, cwd=ROOT)
        minutes = (time.perf_counter() - start) / 60
        if result.returncode != 0:
            log(f"ПОМИЛКА: {name} після {minutes:.1f} хв — зупиняюсь")
            sys.exit(result.returncode)
        log(f"Готово: {name} — {minutes:.1f} хв")
    log(f"Усе готово за {(time.perf_counter() - total_start) / 60:.1f} хв")


if __name__ == "__main__":
    main()