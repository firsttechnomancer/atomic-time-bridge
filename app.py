from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/current-time')
def current_time():
    try:
        r = requests.get("http://worldtimeapi.org/api/timezone/America/New_York", timeout=5)
        data = r.json()
        return jsonify({
            "timestamp": data["datetime"],
            "source": "atomic"
        })
    except Exception as e:
        return jsonify({
            "timestamp": None,
            "source": "error",
            "error": str(e)
        }), 503

if __name__ == '__main__':
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)

