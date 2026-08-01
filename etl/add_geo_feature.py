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
geo_query = "SELECT * FROM geolocation"
geo_df = pd.read_sql(geo_query,engine)

print(geo_df.shape)

geo_avg = geo_df.groupby("geolocation_zip_code_prefix").agg({
    "geolocation_lat":"mean",
    "geolocation_lng":"mean",
}).reset_index()

print(geo_avg.shape)
print(geo_avg.head())

# Load the existing feature table (from build_features.py's aggregation step)
query = """
SELECT
    o.order_id,
    o.order_purchase_timestamp,
    o.order_estimated_delivery_date,
    o.order_delivered_customer_date,
    o.order_status,
    c.customer_zip_code_prefix,
    s.seller_zip_code_prefix
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
WHERE o.order_status = 'delivered'
"""
orders_df = pd.read_sql(query, engine)
print(orders_df.shape)

# Join customer location
orders_df = orders_df.merge(
    geo_avg.rename(columns={
        "geolocation_zip_code_prefix": "customer_zip_code_prefix",
        "geolocation_lat": "customer_lat",
        "geolocation_lng": "customer_lng",
    }),
    on="customer_zip_code_prefix",
    how="left",
)

# Join seller location
orders_df = orders_df.merge(
    geo_avg.rename(columns={
        "geolocation_zip_code_prefix": "seller_zip_code_prefix",
        "geolocation_lat": "seller_lat",
        "geolocation_lng": "seller_lng",
    }),
    on="seller_zip_code_prefix",
    how="left",
)

print(orders_df[["customer_zip_code_prefix", "customer_lat", "customer_lng",
                  "seller_zip_code_prefix", "seller_lat", "seller_lng"]].head())
print(orders_df.isna().sum())


print(orders_df[orders_df["order_delivered_customer_date"].isna()])

import numpy as np

def haversine_distance(lat1, lng1, lat2, lng2):
    R = 6371  # Earth's radius in kilometers
    lat1, lng1, lat2, lng2 = map(np.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

orders_df["distance_km"] = haversine_distance(
    orders_df["customer_lat"], orders_df["customer_lng"],
    orders_df["seller_lat"], orders_df["seller_lng"],
)

print(orders_df["distance_km"].describe())

print(orders_df.nlargest(5, "distance_km")[
    ["order_id", "customer_zip_code_prefix", "seller_zip_code_prefix",
     "customer_lat", "customer_lng", "seller_lat", "seller_lng", "distance_km"]
])

# Brazil's approximate real bounding box
BRAZIL_LAT_MIN, BRAZIL_LAT_MAX = -34, 6
BRAZIL_LNG_MIN, BRAZIL_LNG_MAX = -74, -32

def is_valid_brazil_coord(lat, lng):
    return (lat.between(BRAZIL_LAT_MIN, BRAZIL_LAT_MAX)) & (lng.between(BRAZIL_LNG_MIN, BRAZIL_LNG_MAX))

bad_customer = ~is_valid_brazil_coord(orders_df["customer_lat"], orders_df["customer_lng"])
bad_seller = ~is_valid_brazil_coord(orders_df["seller_lat"], orders_df["seller_lng"])

print("Bad customer coords:", bad_customer.sum())
print("Bad seller coords:", bad_seller.sum())

orders_df.loc[bad_customer | bad_seller, "distance_km"] = np.nan

print(orders_df["distance_km"].describe())

# Add is_late target (reuse same logic as before)
orders_df["is_late"] = (orders_df["order_delivered_customer_date"] > orders_df["order_estimated_delivery_date"]).astype(int)

# Aggregate to one row per order — average distance across items in the same order
geo_features = orders_df.groupby("order_id").agg({
    "distance_km": "mean",
    "is_late": "first",
}).reset_index()

print(geo_features.shape)
print(geo_features["distance_km"].isna().sum())

# Merge in the distance feature
agg_df = agg_df.merge(geo_features[["order_id", "distance_km"]], on="order_id", how="left")

print(agg_df["distance_km"].isna().sum())
