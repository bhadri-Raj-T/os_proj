from flask import Flask, render_template, request, jsonify
import sys
from cronalarmv3 import AlarmSystem
import os

app = Flask(__name__)
alarm_system = AlarmSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/alarms', methods=['GET'])
def get_alarms():
    alarms = []
    jobs = alarm_system.cron.list_jobs()
    if jobs and "No cron jobs exist" not in jobs:
        for line in jobs.splitlines():
            if alarm_system.alarm_prefix in line and "SNOOZE_" not in line:
                time_part = line.split(alarm_system.alarm_prefix)[1].strip()
                hour, minute = time_part[:2], time_part[2:4]
                alarms.append(f"{hour}:{minute}")
    return jsonify(alarms)

@app.route('/api/alarms', methods=['POST'])
def set_alarm():
    data = request.json
    try:
        time_str = data['time']
        message = data.get('message', 'Alarm!')
        hour, minute = map(int, time_str.split(':'))
        alarm_system.set_alarm(hour, minute, message)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/alarms', methods=['DELETE'])
def delete_alarm():
    time_str = request.json['time']
    try:
        hour, minute = map(int, time_str.split(':'))
        alarm_system.cancel_alarm(hour, minute)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    

@app.route('/test_alarm')
def test_alarm():
    os.system(f"python3 {os.path.abspath('cronalarm.py')} --trigger 1234 'Test Alarm'")
    return "Test alarm triggered"

if __name__ == '__main__':
    app.run(debug=True)
