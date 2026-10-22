"""Ціни й дати виходу ігор зі Steam у bronze.steam_appdetails."""
from datetime import datetime, timezone

import dlt
from dlt.sources.helpers import requests

from ingest.common import postgres_destination

API_URL = "https://store.steampowered.com/api/appdetails"
CFG = "sources.steam_appdetails."

COLUMNS = {
    "appid": {"data_type": "bigint", "nullable": False},
    "name": {"data_type": "text"},
    "is_free": {"data_type": "bool"},
    "coming_soon": {"data_type": "bool"},
    "release_date": {"data_type": "text"},
    "currency": {"data_type": "text"},
    "price_initial": {"data_type": "bigint"},
    "price_final": {"data_type": "bigint"},
    "discount_percent": {"data_type": "bigint"},
    "loaded_at": {"data_type": "timestamp"},
}


def to_row(appid, data, loaded_at):
    price = data.get("price_overview") or {}  # у безкоштовних ігор ціни немає
    release = data.get("release_date") or {}
    return {
        "appid": appid,
        "name": data["name"],
        "is_free": data["is_free"],
        "coming_soon": release.get("coming_soon"),
        "release_date": release.get("date"),
        "currency": price.get("currency"),
        "price_initial": price.get("initial"),
        "price_final": price.get("final"),
        "discount_percent": price.get("discount_percent"),
        "loaded_at": loaded_at,
    }


@dlt.resource(
    name="steam_appdetails",
    write_disposition="replace",
    columns=COLUMNS,
    schema_contract={"tables": "evolve", "columns": "freeze", "data_type": "freeze"},
)
def steam_appdetails():
    loaded_at = datetime.now(timezone.utc)
    for appid in dlt.config[CFG + "appids"]:
        response = requests.get(
            API_URL,
            params={
                "appids": appid,
                "cc": dlt.config[CFG + "country"],
                "filters": "basic,price_overview,release_date",
            },
        )
        payload = response.json()[str(appid)]
        if not payload["success"]:
            raise ValueError(f"Steam не віддав дані для appid {appid}")
        yield to_row(appid, payload["data"], loaded_at)


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="steam_appdetails",
        destination=postgres_destination(),
        dataset_name="bronze",
    )
    print(pipeline.run(steam_appdetails()))