"""Ціни ігор у Steam (США, Україна) і курс НБУ у bronze."""
from datetime import datetime, timezone

import dlt
from dlt.sources.helpers import requests

from ingest.common import postgres_destination

STEAM_URL = "https://store.steampowered.com/api/appdetails"
NBU_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
CFG = "sources.steam_appdetails."
CONTRACT = {"tables": "evolve", "columns": "freeze", "data_type": "freeze"}

APPDETAILS_COLUMNS = {
    "appid": {"data_type": "bigint", "nullable": False},
    "country": {"data_type": "text", "nullable": False},
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

NBU_COLUMNS = {
    "currency": {"data_type": "text", "nullable": False},
    "rate_date": {"data_type": "date", "nullable": False},
    "uah_per_unit": {"data_type": "double"},
    "loaded_at": {"data_type": "timestamp"},
}


def to_row(appid, country, data, loaded_at):
    price = data.get("price_overview") or {}  # у безкоштовних ігор ціни немає
    release = data.get("release_date") or {}
    return {
        "appid": appid,
        "country": country,
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
    columns=APPDETAILS_COLUMNS,
    schema_contract=CONTRACT,
)
def steam_appdetails():
    loaded_at = datetime.now(timezone.utc)
    for country in dlt.config[CFG + "countries"]:
        for appid in dlt.config[CFG + "appids"]:
            response = requests.get(
                STEAM_URL,
                params={
                    "appids": appid,
                    "cc": country,
                    "filters": "basic,price_overview,release_date",
                },
            )
            payload = response.json()[str(appid)]
            if not payload["success"]:
                raise ValueError(f"Steam не віддав дані: appid {appid}, країна {country}")
            yield to_row(appid, country, payload["data"], loaded_at)


@dlt.resource(
    name="nbu_rates",
    write_disposition="merge",
    primary_key=["currency", "rate_date"],
    columns=NBU_COLUMNS,
    schema_contract=CONTRACT,
)
def nbu_rates():
    loaded_at = datetime.now(timezone.utc)
    response = requests.get(
        NBU_URL,
        params={"valcode": dlt.config["sources.nbu_rates.currency"], "json": ""},
    )
    for item in response.json():
        yield {
            "currency": item["cc"],
            "rate_date": datetime.strptime(item["exchangedate"], "%d.%m.%Y").date(),
            "uah_per_unit": item["rate"],
            "loaded_at": loaded_at,
        }


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="steam_appdetails",
        destination=postgres_destination(),
        dataset_name="bronze",
    )
    print(pipeline.run([steam_appdetails(), nbu_rates()]))