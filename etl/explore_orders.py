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

#print("shape",orders_df.shape)       # (rows, columns)
print(orders_df.head())      # first 5 rows
print(orders_df.dtypes)      # data type of each column
# Create a new column: True if delivered late, False ["order_estimated_delivery_date"orders_dflo[orders_dfoer_status"] != "delivered","is_late"] = pd.NA
# How many orders were late?print(orders_df["is_late"
#

orders_df["is_late"] = orders_df["order_delivered_customer_date"] > orders_df["order_estimated_delivery_date"]
orders_df["is_late"] = orders_df["is_late"].astype("boolean")  # nullable boolean type
orders_df.loc[orders_df["order_status"] != "delivered", "is_late"] = pd.NA


#
# ].value_counts(dropna=Falsel0)
print(orders_df["is_late"].value_counts())

print(orders_df["order_status"].value_counts())

print(orders_df["is_late"].isna().sum())
