-- IriCast schema: TimescaleDB hypertable + view-uri pentru indicatori de seceta.
-- Prereq: CREATE EXTENSION timescaledb; (pas separat, necesita superuser)
--
-- PRAGURI SI FERESTRE (documentate explicit, conform README):
--   Regula de referinta : precipitatii cumulate 72h < 2.0 mm
--   Regula multi-ind.   : referinta SI temp max 24h > 28.0 °C SI RH min 24h < 55.0 %
--   Fereastra incompleta (date lipsa sau inceput de serie) => NULL = "nedefinit",
--   nu se considera perioada umeda.

CREATE TABLE IF NOT EXISTS measurements (
    ts          TIMESTAMPTZ       NOT NULL,
    station     TEXT              NOT NULL,
    sensor      TEXT              NOT NULL,
    value       DOUBLE PRECISION,           -- NULL cand quality = 'missing'
    unit        TEXT,
    quality     TEXT              NOT NULL DEFAULT 'ok',  -- 'ok' | 'missing'
    received_at TIMESTAMPTZ       NOT NULL DEFAULT now(),
    PRIMARY KEY (ts, station, sensor)
);

SELECT create_hypertable('measurements', 'ts',
    if_not_exists => TRUE, migrate_data => TRUE);

CREATE INDEX IF NOT EXISTS idx_measurements_sensor
    ON measurements (station, sensor, ts DESC);

-- Agregare orara per senzor (view simplu; corect intotdeauna, fara staleness)
CREATE OR REPLACE VIEW measurements_hourly AS
SELECT
    time_bucket(INTERVAL '1 hour', ts) AS hour,
    station,
    sensor,
    avg(value) AS avg_value,
    max(value) AS max_value,
    min(value) AS min_value,
    count(value) AS n_ok,
    count(*) FILTER (WHERE quality = 'missing') AS n_missing
FROM measurements
GROUP BY 1, 2, 3;

-- Pivot orar: un rand pe ora cu toti senzorii statiei
CREATE OR REPLACE VIEW hourly_pivot AS
SELECT
    hour,
    station,
    max(max_value) FILTER (WHERE sensor = 'temperature')     AS temp_c_max,
    min(min_value) FILTER (WHERE sensor = 'humidity')        AS rh_pct_min,
    sum(avg_value)  FILTER (WHERE sensor = 'precipitation')  AS precip_mm_sum,
    avg(avg_value)  FILTER (WHERE sensor = 'soil_moisture')  AS soil_m3_avg,
    sum(n_ok)      AS n_ok,
    sum(n_missing) AS n_missing
FROM measurements_hourly
GROUP BY 1, 2;

-- Indicatori de seceta: regula referinta vs multi-indicator
CREATE OR REPLACE VIEW v_drought AS
SELECT
    hp.hour,
    hp.station,
    hp.precip_mm_sum,
    hp.temp_c_max,
    hp.rh_pct_min,
    hp.soil_m3_avg,
    hp.n_ok,
    hp.n_missing,
    SUM(hp.precip_mm_sum) OVER w72 AS precip_72h_mm,
    MAX(hp.temp_c_max)    OVER w24 AS temp_24h_max,
    MIN(hp.rh_pct_min)    OVER w24 AS rh_24h_min,
    CASE
        WHEN COUNT(hp.precip_mm_sum) OVER w72 >= 72
         AND COUNT(hp.temp_c_max)    OVER w24 >= 24
         AND COUNT(hp.rh_pct_min)    OVER w24 >= 24
        THEN SUM(hp.precip_mm_sum) OVER w72 < 2.0
    END AS dry_ref,
    CASE
        WHEN COUNT(hp.precip_mm_sum) OVER w72 >= 72
         AND COUNT(hp.temp_c_max)    OVER w24 >= 24
         AND COUNT(hp.rh_pct_min)    OVER w24 >= 24
        THEN SUM(hp.precip_mm_sum) OVER w72 < 2.0
         AND MAX(hp.temp_c_max)    OVER w24 > 28.0
         AND MIN(hp.rh_pct_min)    OVER w24 < 55.0
    END AS dry_multi
FROM hourly_pivot hp
WINDOW
    w72 AS (PARTITION BY hp.station ORDER BY hp.hour
            ROWS BETWEEN 71 PRECEDING AND CURRENT ROW),
    w24 AS (PARTITION BY hp.station ORDER BY hp.hour
            ROWS BETWEEN 23 PRECEDING AND CURRENT ROW);
