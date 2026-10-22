"""Extract Our World in Data energy + CO2 files and load them into PostgreSQL (raw layer).

Design:
  * Idempotent: each file's SHA-256 is recorded in raw.load_log; an unchanged file is skipped.
  * Auditable: every load gets a load_id and timestamp; raw tables keep all history.
  * Schema-drift safe: raw tables store each row as JSONB, so new columns published by
    OWID never break the load. dbt picks the columns it needs downstream.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import time
import urllib.request
from datetime import datetime, timezone

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

SOURCES = {
    "owid_energy": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
    "owid_co2": "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv",
}
DEFAULT_URL = "postgresql://postgres:postgres@localhost:5432/gridflow"

DDL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.load_log (
    load_id     BIGSERIAL PRIMARY KEY,
    source      TEXT NOT NULL,
    url         TEXT NOT NULL,
    sha256      TEXT NOT NULL,
    n_rows      INT  NOT NULL,
    n_columns   INT  NOT NULL,
    loaded_at   TIMESTAMPTZ NOT NULL,
    UNIQUE (source, sha256)
);
CREATE TABLE IF NOT EXISTS raw.owid_energy (load_id BIGINT REFERENCES raw.load_log, record JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS raw.owid_co2    (load_id BIGINT REFERENCES raw.load_log, record JSONB NOT NULL);
"""


def fetch(url: str, retries: int = 4) -> bytes:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def to_records(content: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(content), low_memory=False)
    if not {"country", "year"}.issubset(df.columns):
        raise ValueError("source file is missing country/year columns")
    return df


def load_source(conn, source: str, url: str, content: bytes | None = None) -> str:
    content = content if content is not None else fetch(url)
    digest = hashlib.sha256(content).hexdigest()
    with conn.cursor() as cur:
        cur.execute("SELECT load_id FROM raw.load_log WHERE source=%s AND sha256=%s", (source, digest))
        if cur.fetchone():
            return f"{source}: unchanged (sha256 {digest[:12]}), skipped"
        df = to_records(content)
        cur.execute("""INSERT INTO raw.load_log (source, url, sha256, n_rows, n_columns, loaded_at)
                       VALUES (%s,%s,%s,%s,%s,%s) RETURNING load_id""",
                    (source, url, digest, len(df), df.shape[1], datetime.now(timezone.utc)))
        load_id = cur.fetchone()[0]
        records = df.astype(object).where(df.notna(), None).to_dict(orient="records")
        execute_values(cur, f"INSERT INTO raw.{source} (load_id, record) VALUES %s",
                       [(load_id, json.dumps(r)) for r in records], page_size=5000)
    conn.commit()
    return f"{source}: loaded {len(df):,} rows x {df.shape[1]} cols as load_id {load_id}"


def run(database_url: str | None = None) -> list[str]:
    conn = psycopg2.connect(database_url or os.environ.get("DATABASE_URL", DEFAULT_URL))
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()
    return [load_source(conn, s, u) for s, u in SOURCES.items()]
