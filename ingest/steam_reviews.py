"""Інжест відгуків Steam у bronze.steam_reviews."""
import json
import time

import dlt
from dlt.sources.helpers import requests

from ingest.common import FREEZE_CONTRACT, postgres_destination

API_URL = "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/"
DAY = 86400
CFG = "sources.steam_reviews."


def to_row(review, appid):
    author = review["author"]
    return {
        "recommendationid": review["recommendationid"],
        "appid": appid,
        "language": review["language"],
        "review": review["review"].replace("\x00", ""),  # Postgres не приймає символ NUL
        "voted_up": review["voted_up"],
        "timestamp_created": review["timestamp_created"],
        "timestamp_updated": review["timestamp_updated"],
        "author_steamid": author["steamid"],
        "author_num_reviews": author["num_reviews"],
        "author_playtime_at_review": author.get("playtime_at_review"),
    }


def fetch_reviews(appid, language, start, end):
    cursor = "*"
    while True:
        params = {
            "appid": appid,
            "num_per_page": 100,
            "languages": [language],
            "filter": 1,
            "cursor": cursor,
            "date_range_start": start,
            "date_range_end": end,
        }
        response = requests.get(API_URL, params={"input_json": json.dumps(params)})
        data = response.json()["response"]
        reviews = data.get("reviews", [])
        if not reviews:
            break
        yield [to_row(review, appid) for review in reviews]
        cursor = data["cursor"]


def windows(start, end, chunk_days):
    step = chunk_days * DAY
    for chunk_start in range(start, end, step):
        yield chunk_start, min(chunk_start + step, end)


def reviews_resource(appid, language, start, end):
    @dlt.resource(
        name=f"reviews_{appid}_{language}_{start}",
        table_name="steam_reviews",
        write_disposition="merge",
        primary_key="recommendationid",
        parallelized=True,
    )
    def _reviews(created=dlt.sources.incremental("timestamp_created", initial_value=start)):
        yield from fetch_reviews(appid, language, created.last_value, end)

    return _reviews


@dlt.source(
    name="steam_reviews",
    schema_contract=FREEZE_CONTRACT,
)
def steam_reviews_source():
    languages = dlt.config[CFG + "languages"]
    end = dlt.config[CFG + "date_range_end"]
    chunk_days = dlt.config[CFG + "chunk_days"]
    resources = []

    for appid in dlt.config[CFG + "base_appids"]:
        for chunk_start, chunk_end in windows(dlt.config[CFG + "base_start"], end, chunk_days):
            for language in languages:
                resources.append(reviews_resource(appid, language, chunk_start, chunk_end))

    for appid in dlt.config[CFG + "metro_appids"]:
        for language in languages:
            resources.append(reviews_resource(appid, language, dlt.config[CFG + "metro_start"], end))

    return resources


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="steam_reviews",
        destination=postgres_destination(),
        dataset_name="bronze",
        progress="log",
    )
    started = time.perf_counter()
    print(pipeline.run(steam_reviews_source()))
    print(f"Тривалість: {(time.perf_counter() - started) / 60:.1f} хв")