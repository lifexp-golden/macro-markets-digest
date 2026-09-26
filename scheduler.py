import time
import subprocess
from datetime import datetime

# Interval in seconds: 43200 seconds = 12 hours (runs twice a day)
REFRESH_INTERVAL = 43200

while True:
    print(f"[{datetime.now()}] Triggering scheduled digest update...")
    subprocess.run(["python", "generate_digest.py"])
    time.sleep(REFRESH_INTERVAL)
