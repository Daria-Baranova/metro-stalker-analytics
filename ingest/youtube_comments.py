"""Коментарі до трейлерів METRO 2039 з YouTube у bronze.youtube_comments."""
import csv
import os
from pathlib import Path

import dlt
from dlt.sources.helpers import requests

from ingest.common import FREEZE_CONTRACT, postgres_destination

API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
VIDEOS_CSV = Path(__file__).resolve().parents[1] / "dbt" / "seeds" / "videos.csv"

COLUMNS = {
    "comment_id": {"data_type": "text", "nullable": False},
    "video_id": {"data_type": "text", "nullable": False},
    "text": {"data_type": "text"},
    "like_count": {"data_type": "bigint"},
    "published_at": {"data_type": "timestamp"},
    "updated_at": {"data_type": "timestamp"},
}


def read_video_ids():
    with open(VIDEOS_CSV, encoding="utf-8") as file:
        return [row["video_id"] for row in csv.DictReader(file)]


def to_row(item, video_id):
    snippet = item["snippet"]["topLevelComment"]["snippet"]
    return {
        "comment_id": item["id"],
        "video_id": video_id,
        "text": snippet["textDisplay"].replace("\x00", ""),
        "like_count": snippet["likeCount"],
        "published_at": snippet["publishedAt"],
        "updated_at": snippet["updatedAt"],
    }


def fetch_comments(video_id, api_key):
    page_token = None
    while True:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "order": "time",
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token
        response = requests.get(
            API_URL, params=params, headers={"X-Goog-Api-Key": api_key}  # ключ не в URL
        )
        data = response.json()
        yield [to_row(item, video_id) for item in data.get("items", [])]
        page_token = data.get("nextPageToken")
        if not page_token:
            break


@dlt.resource(
    name="youtube_comments",
    write_disposition="merge",
    primary_key="comment_id",
    columns=COLUMNS,
    schema_contract=FREEZE_CONTRACT,
)
def youtube_comments(api_key):
    for video_id in read_video_ids():
        yield from fetch_comments(video_id, api_key)


if __name__ == "__main__":
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print("YOUTUBE_API_KEY немає в .env — пропускаю коментарі YouTube")
    else:
        pipeline = dlt.pipeline(
            pipeline_name="youtube_comments",
            destination=postgres_destination(),
            dataset_name="bronze",
        )
        print(pipeline.run(youtube_comments(api_key)))