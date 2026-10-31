"""Backend IriCast: FastAPI. Ingest batch din gateway + API pentru dashboard/analiza."""
from contextlib import asynccontextmanager
from datetime import datetime

import psycopg
from fastapi import FastAPI, HTTPException, Query
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel

from config import DB_DSN

MAX_BATCH = 1000

pool: ConnectionPool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = ConnectionPool(DB_DSN, min_size=1, max_size=4,
                          kwargs={"row_factory": dict_row}, open=True)
    yield
    pool.close()


app = FastAPI(title="IriCast Backend", version="1.0.0", lifespan=lifespan)


class Measurement(BaseModel):
    station: str
    sensor: str
    value: float | None = None
    unit: str | None = None
    ts: datetime
    quality: str = "ok"


@app.get("/api/health")
def health():
    try:
        with pool.connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "db": "up"}
    except Exception as e:
        raise HTTPException(503, f"db indisponibil: {e}")


@app.post("/ingest")
def ingest(batch: list[Measurement]):
    if not batch:
        return {"inserted": 0}
    if len(batch) > MAX_BATCH:
        raise HTTPException(413, f"batch maxim {MAX_BATCH} măsurători")
    rows = [
        (m.ts, m.station, m.sensor, m.value, m.unit, m.quality)
        for m in batch
    ]
    values_sql = ",".join(["(%s,%s,%s,%s,%s,%s)"] * len(rows))
    flat = [x for r in rows for x in r]
    with pool.connection() as conn:
        cur = conn.execute(
            f"INSERT INTO measurements (ts, station, sensor, value, unit, quality) "
            f"VALUES {values_sql} ON CONFLICT DO NOTHING",
            flat,
        )
        return {"inserted": cur.rowcount}


def _range_filters(start: datetime | None, end: datetime | None,
                   col: str, params: list) -> str:
    where = []
    if start:
        params.append(start)
        where.append(f"{col} >= %s")
    if end:
        params.append(end)
        where.append(f"{col} <= %s")
    return (" AND " + " AND ".join(where)) if where else ""


@app.get("/api/measurements")
def measurements(
    station: str = "buniol",
    sensor: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(1000, ge=1, le=10000),
):
    params: list = [station]
    sql = "SELECT ts, station, sensor, value, unit, quality FROM measurements WHERE station = %s"
    if sensor:
        params.append(sensor)
        sql += " AND sensor = %s"
    sql += _range_filters(start, end, "ts", params)
    sql += " ORDER BY ts DESC LIMIT %s"
    params.append(limit)
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchall()


@app.get("/api/hourly")
def hourly(
    station: str = "buniol",
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(2000, ge=1, le=10000),
):
    params: list = [station]
    extra = _range_filters(start, end, "hour", params)
    sql = (f"SELECT * FROM v_drought WHERE station = %s{extra} "
           f"ORDER BY hour ASC LIMIT %s")
    params.append(limit)
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchall()


@app.get("/api/drought")
def drought(
    station: str = "buniol",
    start: datetime | None = None,
    end: datetime | None = None,
):
    """Randuri orare cu indicatori + sumar comparativ referinta vs multi-indicator."""
    params: list = [station]
    extra = _range_filters(start, end, "hour", params)
    with pool.connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM v_drought WHERE station = %s{extra} ORDER BY hour ASC",
            params,
        ).fetchall()
        summary = conn.execute(
            f"""
            SELECT
                count(*)                                        AS total_hours,
                count(*) FILTER (WHERE dry_ref)                 AS ref_true,
                count(*) FILTER (WHERE dry_multi)               AS multi_true,
                count(*) FILTER (WHERE dry_ref AND dry_multi)   AS both_true,
                count(*) FILTER (WHERE dry_ref AND NOT dry_multi) AS only_ref,
                count(*) FILTER (WHERE NOT dry_ref AND dry_multi) AS only_multi,
                count(*) FILTER (WHERE dry_ref IS NULL OR dry_multi IS NULL)
                                                                AS insufficient_data
            FROM v_drought WHERE station = %s{extra}
            """,
            params,
        ).fetchone()
    return {"summary": summary, "hours": rows}


@app.get("/api/stats")
def stats(station: str = "buniol"):
    with pool.connection() as conn:
        return conn.execute(
            """
            SELECT sensor,
                   count(value)                                    AS n_ok,
                   count(*) FILTER (WHERE quality = 'missing')      AS n_missing,
                   min(ts) AS first_ts,
                   max(ts) AS last_ts
            FROM measurements
            WHERE station = %s
            GROUP BY sensor
            ORDER BY sensor
            """,
            [station],
        ).fetchall()
