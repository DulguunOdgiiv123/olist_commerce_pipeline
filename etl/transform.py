"""
transform.py

Loads raw order and review data from Postgres, applies cleaning/feature
transformations, and writes the result back to Postgres as a new table
(orders_transformed) for downstream analysis and modeling.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd


def get_engine():
    """Build a SQLAlchemy engine from .env credentials."""
    load_dotenv()
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD", "")

    connection_string = (
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    return create_engine(connection_string)


def load_raw_data(engine):
    """Pull the raw tables we need from Postgres into DataFrames."""
    orders_df = pd.read_sql("SELECT * FROM orders", engine)
    reviews_df = pd.read_sql("SELECT * FROM order_reviews", engine)
    return orders_df, reviews_df


def add_delivery_features(orders_df):
    """Add is_late (bool) and delivery_delay_days (int) columns.

    Non-delivered orders are explicitly marked as missing (NA) rather
    than silently counted as on-time.
    """
    df = orders_df.copy()

    df["is_late"] = df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]
    df["is_late"] = df["is_late"].astype("boolean")
    df.loc[df["order_status"] != "delivered", "is_late"] = pd.NA

    df["delivery_delay_days"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.days

    return df


def join_reviews(orders_df, reviews_df):
    """Left-join review data onto orders, keyed on order_id.

    Note: a small number of orders have more than one review, which
    will produce duplicate order rows in the result. We keep only the
    first review per order to avoid inflating row counts.
    """
    reviews_dedup = reviews_df.drop_duplicates(subset="order_id", keep="first")
    merged = orders_df.merge(reviews_dedup, on="order_id", how="left")
    return merged


def save_to_postgres(df, engine, table_name="orders_transformed"):
    """Write the transformed DataFrame back to Postgres as a new table."""
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"Saved {len(df)} rows to table '{table_name}'")


def main():
    engine = get_engine()

    print("Loading raw data...")
    orders_df, reviews_df = load_raw_data(engine)

    print("Adding delivery features...")
    orders_df = add_delivery_features(orders_df)

    print("Joining reviews...")
    merged_df = join_reviews(orders_df, reviews_df)

    print("Summary:")
    print(merged_df["is_late"].value_counts(dropna=False))
    print(merged_df.groupby("is_late")["review_score"].mean())

    save_to_postgres(merged_df, engine)


if __name__ == "__main__":
    main()
