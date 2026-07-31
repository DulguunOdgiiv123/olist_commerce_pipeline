import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Olist Delivery Insights", layout="wide")

@st.cache_data
def load_data():
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD", "")

    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(connection_string)
    return pd.read_sql("SELECT * FROM orders_transformed", engine)

df = load_data()

st.title("📦 Olist Delivery & Review Insights")
st.write(df.shape)
st.dataframe(df.head())

total_orders = len(df)
late_pct = (df["is_late"] == True).mean() * 100
avg_score_ontime = df.loc[df["is_late"] == False, "review_score"].mean()
avg_score_late = df.loc[df["is_late"] == True, "review_score"].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Total Orders", f"{total_orders:,}")
col2.metric("Late Delivery Rate", f"{late_pct:.1f}%")
col3.metric("Review Score Gap", f"{avg_score_ontime - avg_score_late:.2f} stars",
            help="Difference between on-time and late average review scores")

import plotly.express as px

st.subheader("Review Score: On-Time vs Late Deliveries")

score_by_lateness = df.groupby("is_late", dropna=True)["review_score"].mean().reset_index()
score_by_lateness["is_late"] = score_by_lateness["is_late"].map({False: "On Time", True: "Late"})

fig1 = px.bar(
    score_by_lateness,
    x="is_late",
    y="review_score",
    color="is_late",
    labels={"is_late": "Delivery Status", "review_score": "Avg. Review Score"},
    color_discrete_map={"On Time": "#2ecc71", "Late": "#e74c3c"},
)


import plotly.express as px

st.subheader("Review Score: On-Time vs Late Deliveries")

score_by_lateness = df.groupby("is_late", dropna=True)["review_score"].mean().reset_index()
score_by_lateness["is_late"] = score_by_lateness["is_late"].map({False: "On Time", True: "Late"})

fig1 = px.bar(
    score_by_lateness,
    x="is_late",
    y="review_score",
    color="is_late",
    labels={"is_late": "Delivery Status", "review_score": "Avg. Review Score"},
    color_discrete_map={"On Time": "#2ecc71", "Late": "#e74c3c"},
)
st.plotly_chart(fig1, use_container_width=True)
