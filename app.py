from flask import Flask, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

@app.route('/current-time')
def current_time():
    try:
        r = requests.get("http://worldtimeapi.org/api/ip", timeout=5)
        api_time = r.json()["datetime"]
    except:
        api_time = None

    local_time = datetime.now().astimezone().isoformat()

    return jsonify({
        "timestamp_from_api": api_time,
        "timestamp_from_render": local_time
    })
