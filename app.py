from flask import Flask, jsonify
import requests
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Timezone to normalize to
eastern = pytz.timezone("US/Eastern")

# Helper to fetch from worldtimeapi.org
def fetch_worldtimeapi():
    try:
        r = requests.get("http://worldtimeapi.org/api/timezone/America/New_York", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get("datetime"), "atomic1"
    except:
        return None, None
    return None, None

# Helper to fetch from timeapi.io
def fetch_timeapiio():
    try:
        r = requests.get("https://timeapi.io/api/Time/current/zone?timeZone=America/New_York", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get("dateTime"), "atomic2"
    except:
        return None, None
    return None, None

# Helper to use server time
def fetch_local_time():
    try:
        local_dt = datetime.now().astimezone(eastern)
        return local_dt.isoformat(), "local"
    except:
        return None, None

# Normalize timestamp to EST/EDT with DST awareness
def normalize_to_eastern(raw_iso):
    try:
        dt = datetime.fromisoformat(raw_iso.replace("Z", "+00:00"))
        dt = dt.astimezone(eastern)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z%z"), dt.tzname(), dt.utcoffset().total_seconds()
    except:
        return None, None, None

@app.route('/current-time')
def current_time():
    sources = []

    # Try all sources
    t1, s1 = fetch_worldtimeapi()
    if t1:
        sources.append((t1, s1))

    t2, s2 = fetch_timeapiio()
    if t2:
        sources.append((t2, s2))

    t3, s3 = fetch_local_time()
    if t3:
        sources.append((t3, s3))

    # Pick the first successful source
    for timestamp, source in sources:
        try:
            formatted, tzname, offset = normalize_to_eastern(timestamp)
            if formatted:
                return jsonify({
                    "formatted_time": formatted,
                    "tz_label": tzname,
                    "utc_offset_seconds": offset,
                    "source_used": source,
                    "raw": timestamp
                })
        except:
            continue

    # All sources failed
    return jsonify({
        "error": "All time sources failed",
        "source_used": None
    }), 503

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
