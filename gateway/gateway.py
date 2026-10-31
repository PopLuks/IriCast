import json
import threading
import time
from collections import deque

import paho.mqtt.client as mqtt
import requests

from config import BACKEND_URL, MQTT_HOST, MQTT_PORT, STATION_ID

TOPIC_WILDCARD = f"iricast/#"
FLUSH_SIZE = 50
FLUSH_INTERVAL_S = 2.0
MAX_BUFFER = 10_000
STATS_EVERY_S = 10.0

class Gateway:
    def __init__(self) -> None:
        self.buffer: deque[dict] = deque()
        self.lock = threading.Lock()
        self.last_flush = time.monotonic()
        self.backoff = 1.0
        self.stats: dict[str, dict] = {}
        self.malformed = 0
        self.sent_total = 0
        self.stop = threading.Event()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Conectat la broker {MQTT_HOST}:{MQTT_PORT} ({reason_code}); abonat la {TOPIC_WILDCARD}")
        client.subscribe(TOPIC_WILDCARD, qos=1)

    def on_message(self, client, userdata, msg):
        try:
            m = json.loads(msg.payload.decode("utf-8"))
            sensor = m["sensor"]
            m.setdefault("station", STATION_ID)
        except (ValueError, KeyError, UnicodeDecodeError):
            self.malformed += 1
            return
        with self.lock:
            if len(self.buffer) >= MAX_BUFFER:
                self.buffer.popleft()
            self.buffer.append(m)
        st = self.stats.setdefault(sensor, {"received": 0, "last_ts": None})
        st["received"] += 1
        st["last_ts"] = m.get("ts")

    def flush_once(self) -> bool:
        with self.lock:
            if not self.buffer:
                return True
            batch = list(self.buffer)
            self.buffer.clear()
        try:
            r = requests.post(f"{BACKEND_URL}/ingest", json=batch, timeout=10)
            r.raise_for_status()
            inserted = r.json().get("inserted", 0)
        except Exception as e:
            with self.lock:
                for item in reversed(batch):
                    self.buffer.appendleft(item)
            print(f"ingest esuat ({e}); retry in {self.backoff:.0f}s, buffer={len(self.buffer)}")
            return False
        self.sent_total += len(batch)
        print(f"batch {len(batch)} mesaje -> {inserted} randuri noi (total {self.sent_total})")
        return True

    def flusher_loop(self):
        while not self.stop.is_set():
            with self.lock:
                due = len(self.buffer) >= FLUSH_SIZE or (
                    self.buffer and time.monotonic() - self.last_flush >= FLUSH_INTERVAL_S
                )
            ok = True
            if due:
                ok = self.flush_once()
                self.last_flush = time.monotonic()
            if ok:
                self.backoff = 1.0
            else:
                time.sleep(self.backoff)
                self.backoff = min(self.backoff * 2, 60.0)
            time.sleep(0.2)

    def stats_loop(self):
        last_sent = 0
        while not self.stop.is_set():
            time.sleep(STATS_EVERY_S)
            rate = (self.sent_total - last_sent) / STATS_EVERY_S
            last_sent = self.sent_total
            lines = [
                f"  {name}: primit={st['received']} ultim_ts={st['last_ts']}"
                for name, st in sorted(self.stats.items())
            ]
            print(f"[stats] senzori activi={len(self.stats)} ratie={rate:.1f} msg/s "
                  f"malforme={self.malformed}")
            print("\n".join(lines))

    def run(self):
        cli = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="iricast-gateway",
        )
        cli.on_connect = self.on_connect
        cli.on_message = self.on_message
        cli.reconnect_delay_set(min_delay=1, max_delay=60)
        cli.connect(MQTT_HOST, MQTT_PORT)

        flusher = threading.Thread(target=self.flusher_loop, daemon=True)
        stats = threading.Thread(target=self.stats_loop, daemon=True)
        flusher.start()
        stats.start()

        print(f"Gateway pornit; ingest catre {BACKEND_URL}/ingest")
        try:
            cli.loop_forever()
        except KeyboardInterrupt:
            print("Opire gateway...")
            self.stop.set()
            cli.loop_stop()
            cli.disconnect()
            if self.buffer:
                print(f"flush final ({len(self.buffer)} mesaje)...")
                self.flush_once()


if __name__ == "__main__":
    Gateway().run()
