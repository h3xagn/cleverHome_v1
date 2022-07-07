"""
Electricity monitoring notifications using Telegram bot

1. Get current power measurement and add the queue
2. Determine if the power state has change and send notification if needed
"""
# import libraries
import os
import requests
import time
from datetime import datetime
from collections import deque

# define initial values
measurements = deque(maxlen=3)
mains_power_state = True

# load environmental variables
bot_token = os.getenv("TELEGRAM_BOT")
chat_id = os.getenv("TELEGRAM_CROUP")
efergy_token = os.getenv("EFERGY_TOKEN")


def SendTelegramMessage(message):
    """Send a Telegram message to the group"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": f"{chat_id}", "text": message, "parse_mode": "MarkdownV2"}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


def GetPowerMeasurement():
    """Get the current power reading from the efergy device"""
    try:
        url = f"http://www.energyhive.com/mobile_proxy/getCurrentValuesSummary?token={efergy_token}"
        response = requests.get(url)
        data = response.json()[0]["data"][0]
        timestamp = datetime.fromtimestamp(int(list(data.keys())[0]) / 1000)
        measurement = list(data.values())[0]
        print(f"Power measurement at {timestamp} was {measurement}W.")
        return measurement
    except Exception as e:
        print(f"Error getting power measurement: {e}")
        return None


# while loop to get power measurements and determine if the power state has changed every 60 seconds
while True:
    # append the measurement to the queue
    measurement = GetPowerMeasurement()
    if measurement is not None:
        measurements.appendleft(measurement)

    # if we have 3 measurements, check if the power state has changed
    if len(measurements) == 3:
        if all(measurement == 0 for measurement in measurements):
            if mains_power_state:
                SendTelegramMessage("Mains power is OFF")
                mains_power_state = False
        if all(measurement > 0 for measurement in measurements):
            if not mains_power_state:
                SendTelegramMessage("Mains power is ON")
                mains_power_state = True

    # use first two readings to confirm the current power state
    elif len(measurements) == 2:
        if all(measurement == 0 for measurement in measurements):
            mains_power_state = False
        if all(measurement > 0 for measurement in measurements):
            mains_power_state = True

    time.sleep(60)
