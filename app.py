from flask import Flask, jsonify
import os

app = Flask(__name__)

SLOT = os.environ.get('SLOT', 'unknown')

@app.route('/')
def home():
    return jsonify({
        "message": f"Hello from {SLOT.upper()} slot!",
        "slot": SLOT,
        "status": "running"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "slot": SLOT}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
