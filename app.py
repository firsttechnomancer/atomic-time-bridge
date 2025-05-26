from flask import Flask, jsonify
from datetime import datetime, timezone, timedelta
import pytz
import ntplib
import os

app = Flask(__name__)
eastern = pytz.timezone("US/Eastern")

# Try NIST atomic clock via NTP
def fetch_ntp_utc():
    try:
        client = ntplib.NTPClient()
        response = client.request('time.nist.gov', version=3)
        utc_dt = datetime.utcfromtimestamp(response.tx_time).replace(tzinfo=timezone.utc)
        return utc_dt, "ntp"
    except:
        return None, None

# Format and convert to Eastern Time
def convert_to_eastern(utc_dt):
    est_dt = utc_dt.astimezone(eastern)
    return {
        "formatted_time": est_dt.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
        "tz_label": est_dt.tzname(),
        "utc_offset_seconds": est_dt.utcoffset().total_seconds(),
        "converted_from_utc": utc_dt.isoformat(),
        "object_dt": est_dt
    }

# Local UTC for drift check
def system_utc():
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

@app.route('/current-time')
def current_time():
    utc_dt, source = fetch_ntp_utc()
    if not utc_dt:
        return jsonify({
            "error": "NTP time failed",
            "render_utc": system_utc()
        }), 503

    result = convert_to_eastern(utc_dt)
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    drift = abs((now_utc - utc_dt).total_seconds())

    return jsonify({
        "formatted_time": result["formatted_time"],
        "tz_label": result["tz_label"],
        "utc_offset_seconds": result["utc_offset_seconds"],
        "source_used": source,
        "converted_from_utc": result["converted_from_utc"],
        "render_utc": system_utc(),
        "drift_vs_system_utc_seconds": drift
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
