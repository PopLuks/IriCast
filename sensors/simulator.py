import argparse
import json
import threading
import time

import pandas as pd
import paho.mqtt.client as mqtt

from config import MQTT_HOST, MQTT_PORT, SENSOR_UNITS, SENSORS, STATION_ID, TOPIC_PREFIX


def build_client() -> mqtt.Client:
    cli = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"iricast-simulator-{STATION_ID}",
    )
    cli.reconnect_delay_set(min_delay=1, max_delay=60)
    return cli


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulator senzori virtuali IriCast")
    ap.add_argument("--dataset", default="data/buniol_dataset.csv")
    ap.add_argument(
        "--speed",
        type=float,
        default=24.0,
        help="ore de date simulate pe secunda reala (1/3600 = timp real; default 24)",
    )
    ap.add_argument("--loop", action="store_true", help="reia datasetul de la inceput la final")
    args = ap.parse_args()

    df = pd.read_csv(args.dataset)
    unknown = [c for c in SENSORS if c not in df.columns]
    if unknown:
        raise SystemExit(f"Datasetul nu are coloanele: {unknown}")

    connected = threading.Event()
    cli = build_client()
    cli.on_connect = lambda c, u, f, rc, props: connected.set()
    cli.connect(MQTT_HOST, MQTT_PORT)
    cli.loop_start()
    if not connected.wait(timeout=10):
        raise SystemExit(f"Nu ma pot conecta la broker {MQTT_HOST}:{MQTT_PORT}")
    print(f"Conectat la {MQTT_HOST}:{MQTT_PORT}; public {len(SENSORS)} senzori pe {TOPIC_PREFIX}/<sensor>")

    interval = 1.0 / args.speed  # un rand = 1 ora simulata
    n_rows = len(df)
    print(f"Dataset: {n_rows} ore simulate, speed={args.speed} h/s, ~{n_rows / args.speed:.0f}s per trecere")

    try:
        while True:
            for i, row in enumerate(df.itertuples(index=False)):
                ts = pd.to_datetime(row.time, utc=True).isoformat()
                for sensor in SENSORS:
                    raw = getattr(row, sensor)
                    missing = pd.isna(raw)
                    payload = {
                        "station": STATION_ID,
                        "sensor": sensor,
                        "value": None if missing else round(float(raw), 4),
                        "unit": SENSOR_UNITS[sensor],
                        "ts": ts,
                        "quality": "missing" if missing else "ok",
                    }
                    cli.publish(f"{TOPIC_PREFIX}/{sensor}", json.dumps(payload), qos=1)
                if i % 24 == 0:
                    print(f"sim {ts}  ({i + 1}/{n_rows} ore)")
                time.sleep(interval)
            if not args.loop:
                break
            print("Dataset terminat; replay de la inceput (--loop)")
    except KeyboardInterrupt:
        print("Simulator oprit.")
    finally:
        cli.loop_stop()
        cli.disconnect()


if __name__ == "__main__":
    main()
