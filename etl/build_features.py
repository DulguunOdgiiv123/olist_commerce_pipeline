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


import numpy as np

def haversine_distance(lat1, lng1, lat2, lng2):
    R = 6371
    lat1, lng1, lat2, lng2 = map(np.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

BRAZIL_LAT_MIN, BRAZIL_LAT_MAX = -34, 6
BRAZIL_LNG_MIN, BRAZIL_LNG_MAX = -74, -32

def is_valid_brazil_coord(lat, lng):
    return (lat.between(BRAZIL_LAT_MIN, BRAZIL_LAT_MAX)) & (lng.between(BRAZIL_LNG_MIN, BRAZIL_LNG_MAX))

query = """
SELECT
    o.order_id,
    o.order_purchase_timestamp,
    o.order_estimated_delivery_date,
    o.order_delivered_customer_date,
    o.order_status,
    c.customer_state,
    oi.price,
    oi.freight_value,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    s.seller_state,
    c.customer_zip_code_prefix,
    s.seller_zip_code_prefix
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN sellers s ON oi.seller_id = s.seller_id
WHERE o.order_status = 'delivered'
"""

df = pd.read_sql(query, engine)

df = pd.read_sql(query, engine)

# --- Load and prep geolocation data ---
geo_df = pd.read_sql("SELECT * FROM geolocation", engine)
geo_avg = geo_df.groupby("geolocation_zip_code_prefix").agg({
    "geolocation_lat": "mean",
    "geolocation_lng": "mean",
}).reset_index()

# Join customer location
df = df.merge(
    geo_avg.rename(columns={
        "geolocation_zip_code_prefix": "customer_zip_code_prefix",
        "geolocation_lat": "customer_lat",
        "geolocation_lng": "customer_lng",
    }),
    on="customer_zip_code_prefix", how="left",
)

# Join seller location
df = df.merge(
    geo_avg.rename(columns={
        "geolocation_zip_code_prefix": "seller_zip_code_prefix",
        "geolocation_lat": "seller_lat",
        "geolocation_lng": "seller_lng",
    }),
    on="seller_zip_code_prefix", how="left",
)

# Compute distance, discard rows with impossible coordinates
df["distance_km"] = haversine_distance(df["customer_lat"], df["customer_lng"], df["seller_lat"], df["seller_lng"])
bad_customer = ~is_valid_brazil_coord(df["customer_lat"], df["customer_lng"])
bad_seller = ~is_valid_brazil_coord(df["seller_lat"], df["seller_lng"])
df.loc[bad_customer | bad_seller, "distance_km"] = np.nan

agg_df = df.groupby("order_id").agg({
    "order_purchase_timestamp": "first",
    "order_estimated_delivery_date": "first",
    "order_delivered_customer_date": "first",
    "order_status": "first",
    "customer_state": "first",
    "seller_state": "first",
    "price": "sum",
    "freight_value": "sum",
    "product_weight_g": "sum",
    "product_length_cm": "sum",
    "product_height_cm": "sum",
    "product_width_cm": "sum",
    "distance_km": "mean",
}).reset_index()



# Target variable
agg_df["is_late"] = (agg_df["order_delivered_customer_date"] > agg_df["order_estimated_delivery_date"]).astype(int)

# Feature: how many days between purchase and estimated delivery (how ambitious was the promise?)
agg_df["estimated_delivery_days"] = (
    agg_df["order_estimated_delivery_date"] - agg_df["order_purchase_timestamp"]
).dt.days

# Feature: day of week the order was purchased (0=Monday, 6=Sunday)
agg_df["purchase_dayofweek"] = agg_df["order_purchase_timestamp"].dt.dayofweek

# Feature: month purchased (seasonality — e.g. holidays might mean more delays)
agg_df["purchase_month"] = agg_df["order_purchase_timestamp"].dt.month

# Feature: same state or different state shipping
agg_df["same_state"] = (agg_df["customer_state"] == agg_df["seller_state"]).astype(int)

print(agg_df[["is_late", "estimated_delivery_days", "purchase_dayofweek", "purchase_month", "same_state"]].head())

feature_cols = [
    "price",
    "freight_value",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
    "estimated_delivery_days",
    "purchase_dayofweek",
    "purchase_month",
    "same_state",
    "distance_km",
]

X = agg_df[feature_cols].copy()
X["distance_km"] = X["distance_km"].fillna(X["distance_km"].median())
y = agg_df["is_late"]
print(X.isna().sum())
print(y.value_counts())

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(X_train.shape, X_test.shape)
print(y_train.value_counts(normalize=True))
print(y_test.value_counts(normalize=True))


from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))

import joblib

joblib.dump(model, "models/late_delivery_model.pkl")
print("Model saved.")

importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print(importances)
