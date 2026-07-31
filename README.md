# Olist E-Commerce ETL Pipeline & Late Delivery Prediction

An end-to-end data pipeline built on the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce): raw CSVs → PostgreSQL → Python/pandas transformations → a scikit-learn model predicting late deliveries.

## Project Goal

E-commerce delivery reliability directly affects customer satisfaction. This project investigates two questions:

1. **How much does a late delivery actually hurt customer reviews?**
2. **Can we predict, before an order ships, whether it's likely to be late?**

## Architecture


Kaggle CSVs (9 files)
│
▼
PostgreSQL (9 raw tables, FK-constrained schema)
│
▼
Python / pandas (etl/transform.py, etl/build_features.py)
│
▼
PostgreSQL (orders_transformed) + scikit-learn model


## Tech Stack

- **PostgreSQL** — relational storage with enforced foreign key constraints
- **Python** (pandas, SQLAlchemy, psycopg2) — extraction and transformation
- **scikit-learn** — Random Forest classifier for late-delivery prediction
- **Git** — version-controlled, reproducible pipeline

## Key Findings

### Late delivery devastates review scores

| Delivery status | Avg. review score (out of 5) |
|---|---|
| On time | 4.30 |
| Late | 2.56 |

Across 96,478 delivered orders, ~8.1% arrived after the estimated delive1ry date — and those orders scored nearly **1.75 points lower** on average. This is one of the clearest signals in the dataset: delivery reliability appears to be a dominant driver of customer satisfaction.

### Predicting late delivery: a Random Forest classifier

Using pre-delivery features only (price, freight value, product dimensions/weight, estimated delivery window, purchase timing, same-state shipping), a Random Forest was trained to predict `is_late`.

**Results (on a held-out 20% test set, class-weighted for imbalance):**

| Metric (late-delivery class) | Score |
|---|---|
| Precision | 0.30 |
| Recall | 0.17 |
| Overall accuracy | 0.90 |

**Honest interpretation:** overall accuracy (90%) is misleading here, since the dataset is ~92% on-time by default — a model that always predicted "on time" would already score close to that. The more meaningful metrics are precision/recall on the late class, and this first model only catches 17% of actual late deliveries. This suggests the available order-level features (price, weight, timing) are only weakly predictive of lateness on their own.

**Feature importance** (top 3): `freight_value`, `estimated_delivery_days`, `price`. Notably, a simple `same_state` binary flag was the weakest feature (0.015) — a poor proxy for actual shipping distance. A likely next step to meaningfully improve the model would be computing real geographic distance using the geolocation table, since carrier logistics (not order characteristics) are probably the dominant cause of delays.

## Data Quality Handling

Two real data issues were identified and resolved during the load phase:

- **Missing category translations:** a handful of `product_category_name` values (e.g. `pc_gamer`) had no matching row in the translation table. Loaded via a staging table + `LEFT JOIN`, nulling out unmatched categories rather than dropping the products entirely.
- **Duplicate review IDs:** a small number of `review_id`s appeared more than once in the raw CSV. Deduplicated using `DISTINCT ON`, keeping the earliest occurrence per review.

## Project Structure

olist-pipeline/
├── data/raw/ # source CSVs (not committed — see Setup)
├── sql/schema.sql # PostgreSQL schema with FK constraints
├── etl/
│ ├── transform.py # loads raw data, builds delivery features, joins reviews
│ └── build_features.py # builds ML feature set, trains Random Forest model
├── models/ # trained model artifacts (not committed, see .gitignore)
└── README.md


## Setup & Reproduction

1. Download the [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) into `data/raw/`
2. Create a PostgreSQL database and run the schema:
```bash
   createdb olist
   psql -d olist -f sql/schema.sql
```
3. Load the CSVs (see `sql/` for `\copy` commands used)
4. Set up a Python virtual environment and install dependencies:
```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install pandas sqlalchemy psycopg2-binary python-dotenv scikit-learn joblib
```
5. Create a `.env` file with your database credentials
6. Run the pipeline:
```bash
   python etl/transform.py
   python etl/build_features.py
```

## Next Steps

- Add real geographic distance (via the geolocation table) as a feature
- Try gradient boosting (XGBoost/LightGBM) as a comparison model
- Build a BI dashboard (Power BI) summarizing the delivery/review relationship
