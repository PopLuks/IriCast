import os
from dotenv import load_dotenv

load_dotenv()

STATION_ID = os.getenv("IRICAST_STATION_ID", "buniol")
STATION_NAME = os.getenv("IRICAST_STATION_NAME", "Buniol")
LAT = float(os.getenv("IRICAST_LAT", "47.205624"))
LON = float(os.getenv("IRICAST_LON", "26.427406"))

MQTT_HOST = os.getenv("IRICAST_MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("IRICAST_MQTT_PORT", "1883"))
TOPIC_PREFIX = f"iricast/{STATION_ID}"

BACKEND_URL = os.getenv("IRICAST_BACKEND_URL", "http://127.0.0.1:8000")

_DB_USER = os.getenv("IRICAST_DB_USER", "iricast")
_DB_PASSWORD = os.getenv("IRICAST_DB_PASSWORD", "iricast")
_DB_HOST = os.getenv("IRICAST_DB_HOST", "127.0.0.1")
_DB_PORT = os.getenv("IRICAST_DB_PORT", "5432")
_DB_NAME = os.getenv("IRICAST_DB_NAME", "iricast")
DB_DSN = os.getenv(
    "IRICAST_DB_DSN",
    f"postgresql://{_DB_USER}:{_DB_PASSWORD}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}",
)

SENSORS = ["temperature", "humidity", "precipitation", "soil_moisture"]
SENSOR_UNITS = {
    "temperature": "°C",
    "humidity": "%",
    "precipitation": "mm",
    "soil_moisture": "m3/m3",
}

PRECIP_WINDOW_H = 72
PRECIP_DRY_MM = 2.0
TEMP_WINDOW_H = 24
TEMP_HOT_C = 28.0
RH_WINDOW_H = 24
RH_DRY_PCT = 55.0