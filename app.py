from flask import Flask, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/current-time')
def current_time():
    try:
        # Get atomic time from worldtimeapi (auto-detect timezone by IP)
        r = requests.get("http://worldtimeapi.org/api/ip", timeout=5)
        api_time = r.json()["datetime"]
    except Exception as e:
        api_time = f"ERROR: {str(e)}"

    # Get local server time (Render's clock)
    local_time = datetime.now().astimezone().isoformat()

    return jsonify({
        "timestamp_from_api": api_time,
        "timestamp_from_render": local_time
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
