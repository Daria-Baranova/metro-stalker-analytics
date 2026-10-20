"""Інжест відгуків Steam у bronze.steam_reviews."""
import json

import dlt
from dlt.sources.helpers import requests  # requests з повторами при 429

from ingest.common import postgres_destination

API_URL = "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/"


def fetch_reviews(appid, language, start, end):
    """Віддає відгуки сторінка за сторінкою, поки вони є."""
    cursor = "*"  # "*" = перша сторінка
    while True:
        params = {
            "appid": appid,
            "num_per_page": 100,
            "languages": [language],
            "filter": 1,  # Recent
            "cursor": cursor,
            "date_range_start": start,
            "date_range_end": end,
        }
        # timeout і повтори беруться з [runtime] у config.toml
        response = requests.get(API_URL, params={"input_json": json.dumps(params)})
        data = response.json()["response"]

        reviews = data.get("reviews", [])
        if not reviews:  # порожня сторінка = кінець
            break

        for review in reviews:
            review["appid"] = appid  # API не повертає appid — додаємо самі
        yield reviews

        cursor = data["cursor"]  # закладка на наступну сторінку


def reviews_resource(appid, language, start, end):

    @dlt.resource(
        name=f"reviews_{appid}_{language}_{start}",  # унікальне ім'я = свій стан
        table_name="steam_reviews",                   # усі пишуть в одну таблицю
        write_disposition="merge",                    # без дублів
        primary_key="recommendationid",
    )
    def _reviews(
        created=dlt.sources.incremental("timestamp_created", initial_value=start)
    ):
        # Перший запуск: від start. Повторний: від останнього завантаженого
        yield from fetch_reviews(appid, language, created.last_value, end)

    return _reviews


if __name__ == "__main__":
    start = dlt.config["sources.steam_reviews.base_start"]
    end = dlt.config["sources.steam_reviews.date_range_end"]

    pipeline = dlt.pipeline(
        pipeline_name="steam_reviews",
        destination=postgres_destination(),
        dataset_name="bronze",  # схема в Postgres
    )

    # Тест: Far Cry 5, italian (~133 відгуки, 2 сторінки)
    print(pipeline.run(reviews_resource(552520, "italian", start, end)))