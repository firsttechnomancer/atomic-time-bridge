from flask import Flask, jsonify
import requests
from datetime import datetime, timezone
import pytz
import os
import time

app = Flask(__name__)

eastern = pytz.timezone("US/Eastern")

# --- External time sources ---

def fetch_worldtimeapi():
    for _ in range(2):  # Retry twice
        try:
            r = requests.get("http://worldtimeapi.org/api/timezone/America/New_York", timeout=5)
            if r.status_code == 200:
                return r.json().get("datetime"), "atomic1"
        except:
            time.sleep(0.5)
    return None, None

def fetch_timeapiio():
    for _ in range(2):
        try:
            r = requests.get("https://timeapi.io/api/Time/current/zone?timeZone=America/New_York", timeout=5)
            if r.status_code == 200:
                return r.json().get("dateTime"), "atomic2"
        except:
            time.sleep(0.5)
    return None, None

# --- Time formatting ---

def normalize_to_est(raw_iso):
    try:
        dt = datetime.fromisoformat(raw_iso.replace("Z", "+00:00"))
        dt = dt.astimezone(eastern)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z%z"), dt.tzname(), dt.utcoffset().total_seconds(), dt
    except:
        return None, None, None, None

# --- UTC + EST from Render system (reference only) ---

def system_reference_times():
    try:
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        local_est = utc_now.astimezone(eastern)
        return {
            "render_utc": utc_now.isoformat(),
            "render_est": local_est.isoformat()
        }
    except:
        return {}

@app.route('/current-time')
def current_time():
    sources = []

    # Try both atomic APIs
    t1, s1 = fetch_worldtimeapi()
    if t1:
        sources.append((t1, s1))

    t2, s2 = fetch_timeapiio()
    if t2:
        sources.append((t2, s2))

    # Normalize all sources to EST
    for raw, source in sources:
        formatted, tz_label, offset_sec, dt = normalize_to_est(raw)
        if formatted:
            # Also compare to system UTC
            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            drift = abs((now_utc - dt.astimezone(timezone.utc)).total_seconds())

            if drift <= 120:  # Accept only if drift < 2 minutes
                return jsonify({
                    "formatted_time": formatted,
                    "tz_label": tz_label,
                    "utc_offset_seconds": offset_sec,
                    "source_used": source,
                    "raw": raw,
                    "render_utc": system_reference_times().get("render_utc"),
                    "drift_vs_system_utc_seconds": drift
                })

    # All sources failed or drift too large
    return jsonify({
        "error": "No valid source passed drift check",
        "render_utc": system_reference_times().get("render_utc")
    }), 503

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
