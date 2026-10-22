"""Tests for the extract-load step. The database tests need PostgreSQL (see README)."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gridflow.extract_load import DDL, load_source, to_records

CSV_V1 = b"country,year,iso_code,coal_electricity\nUnited Kingdom,2023,GBR,3.1\nFrance,2023,FRA,0.4\n"
CSV_V2 = CSV_V1 + b"Germany,2023,DEU,95.0\n"


def test_to_records_requires_country_and_year():
    with pytest.raises(ValueError):
        to_records(b"a,b\n1,2\n")
    assert len(to_records(CSV_V1)) == 2


@pytest.fixture
def conn():
    psycopg2 = pytest.importorskip("psycopg2")
    url = os.environ.get("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gridflow_test")
    try:
        c = psycopg2.connect(url)
    except Exception:
        pytest.skip("PostgreSQL test database not available")
    with c.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS raw CASCADE"); cur.execute(DDL)
    c.commit()
    yield c
    c.close()


def _count(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql); return cur.fetchone()[0]


def test_load_is_idempotent(conn):
    assert "loaded 2 rows" in load_source(conn, "owid_energy", "test://v1", CSV_V1)
    assert "unchanged" in load_source(conn, "owid_energy", "test://v1", CSV_V1)
    assert _count(conn, "SELECT COUNT(*) FROM raw.owid_energy") == 2
    assert _count(conn, "SELECT COUNT(*) FROM raw.load_log") == 1


def test_new_file_version_is_appended_not_overwritten(conn):
    load_source(conn, "owid_energy", "test://v1", CSV_V1)
    load_source(conn, "owid_energy", "test://v2", CSV_V2)
    assert _count(conn, "SELECT COUNT(*) FROM raw.load_log") == 2
    assert _count(conn, "SELECT COUNT(*) FROM raw.owid_energy") == 5   # history kept
    assert _count(conn, """SELECT COUNT(*) FROM raw.owid_energy
                           WHERE load_id = (SELECT MAX(load_id) FROM raw.load_log)""") == 3


def test_missing_values_become_json_null(conn):
    load_source(conn, "owid_energy", "test://na", b"country,year,iso_code,coal_electricity\nX,2020,XXX,\n")
    assert _count(conn, "SELECT COUNT(*) FROM raw.owid_energy WHERE record->'coal_electricity' = 'null'::jsonb") == 1
