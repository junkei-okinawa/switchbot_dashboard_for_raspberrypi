import os
import asyncio
import logging

import schedule
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from switchbot.discovery import GetSwitchbotDevices
import dbus.exceptions

# Logging
formatter = "[%(levelname)-8s] %(asctime)s %(funcName)s %(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)
logger = logging.getLogger(__name__)

load_dotenv(".env")

# InfluxDB
INFLUXDB_TOKEN = os.environ["INFLUXDB_TOKEN"]
bucket = "switchbot"
client = InfluxDBClient(url="http://influxdb:8086", token=INFLUXDB_TOKEN, org="org")
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

# SwitchBot

def save_device_status(status: dict, device_id: str, device_name: str):
    """SwitchbotデバイスのステータスをInfluxDBに保存する"""
    logging.info(f"Save: {status}")
    p = (
        Point(device_name)
        .tag("device_id", device_id)
        .field("humidity", float(status["humidity"]))
        .field("temperature", float(status["temperature"]))
    )

    if "battery" in status:
        p = p.field("battery", float(status["battery"]))

    write_api.write(bucket=bucket, record=p)
    logging.info(f"Saved: {status}")

async def task():
    """定期実行するタスク"""
    logging.info("Run task")
    sensors = await GetSwitchbotDevices().get_tempsensors()
    for address in sensors:
        try:
            status = sensors[address].data['data']
            device_id = sensors[address].address
            device_name = sensors[address].data['modelFriendlyName']
            save_device_status(status, device_id, device_name)
        except Exception as e:
            if isinstance(e, dbus.exceptions.DBusException):
                logging.error(f"D-Bus error: {e}. Ensure D-Bus socket is mounted and container has necessary privileges.")
            else:
                logging.error(f"Save error: {e}")

async def main():
    logging.info("Start main")
    schedule.every(5).minutes.do(lambda: asyncio.create_task(task()))
    logging.info("Set schedule")

    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

if __name__ == "__main__":
    logging.info("Start")
    asyncio.run(main())
