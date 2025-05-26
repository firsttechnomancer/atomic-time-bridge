from flask import Flask, jsonify
import requests
from datetime import datetime, timezone, timedelta
import pytz
import os
import time

app = Flask(__name__)
eastern = pytz.timezone("US/Eastern")

# -- API SOURCES --

def fetch_worldtimeapi():
    for _ in range(2):
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

# -- NORMALIZE: Force UTC → EST/EDT with pytz

def normalize_utc_to_est(raw_iso):
    try:
        # Always assume input is UTC, then correct
        utc_dt = datetime.fromisoformat(raw_iso.replace("Z", "+00:00")).astimezone(timezone.utc)
        corrected_utc = utc_dt - timedelta(seconds=420)  # subtract 7 minutes
        est_dt = corrected_utc.astimezone(eastern)

        return {
            "formatted_time": est_dt.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
            "tz_label": est_dt.tzname(),
            "utc_offset_seconds": est_dt.utcoffset().total_seconds(),
            "converted_from_utc": corrected_utc.isoformat(),
            "raw_input": raw_iso,
            "object_dt": est_dt,
            "correction_applied": True,
            "utc_offset_adjustment_seconds": -420
        }
    except:
        return None


# -- SYSTEM UTC REFERENCE

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

# -- MAIN ENDPOINT

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

    # Normalize and check drift
    for raw, source in sources:
        result = normalize_utc_to_est(raw)
        if result:
            dt = result["object_dt"]
            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            drift = abs((now_utc - dt.astimezone(timezone.utc)).total_seconds())

            if drift <= 120:
                return jsonify({
                    "formatted_time": result["formatted_time"],
                    "tz_label": result["tz_label"],
                    "utc_offset_seconds": result["utc_offset_seconds"],
                    "source_used": source,
                    "converted_from_utc": result["converted_from"],
                    "raw": result["raw_input"],
                    "render_utc": system_reference_times().get("render_utc"),
                    "drift_vs_system_utc_seconds": drift
                })

    # All sources failed or drifted
    return jsonify({
        "error": "No valid source passed drift check",
        "render_utc": system_reference_times().get("render_utc")
    }), 503

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
