import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)

# TODO: write a SQL query as a string that selects everything from the "orders" table
query = "SELECT * FROM orders"

orders_df = pd.read_sql(query, engine)


orders_df["is_late"] = orders_df["order_delivered_customer_date"] > orders_df["order_estimated_delivery_date"]
orders_df["is_late"] = orders_df["is_late"].astype("boolean")  # nullable boolean type
orders_df.loc[orders_df["order_status"] != "delivered", "is_late"] = pd.NA
orders_df["delivery_delay_days"] = (orders_df["order_delivered_customer_date"] - orders_df["order_estimated_delivery_date"]).dt.days




reviews_query = "SELECT * FROM order_reviews"
reviews_df = pd.read_sql(reviews_query, engine)

merged_df = orders_df.merge(reviews_df, on="order_id",how="left")

avg_score_by_lateness = merged_df.groupby("is_late")["review_score"].mean()

print(avg_score_by_lateness)
