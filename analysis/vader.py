"""Оцінка настрою коментарів YouTube за VADER у bronze.comment_sentiment."""
import dlt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from ingest.common import FREEZE_CONTRACT, postgres_connection, postgres_destination

QUERY = "select comment_id, text from bronze.youtube_comments"

COLUMNS = {
    "comment_id": {"data_type": "text", "nullable": False},
    "compound": {"data_type": "double"},
}


def read_comments():
    connection = postgres_connection()
    with connection, connection.cursor() as cursor:
        cursor.execute(QUERY)
        rows = cursor.fetchall()
    connection.close()
    return rows


@dlt.resource(
    name="comment_sentiment",
    write_disposition="replace",
    primary_key="comment_id",
    columns=COLUMNS,
    schema_contract=FREEZE_CONTRACT,
)
def comment_sentiment():
    analyzer = SentimentIntensityAnalyzer()
    for comment_id, text in read_comments():
        yield {"comment_id": comment_id, "compound": analyzer.polarity_scores(text or "")["compound"]}


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="comment_sentiment",
        destination=postgres_destination(),
        dataset_name="bronze",
    )
    print(pipeline.run(comment_sentiment()))