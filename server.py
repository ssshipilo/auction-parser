from flask import Flask, send_from_directory, render_template, jsonify
import os
import subprocess
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
scheduler = APScheduler()

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

def run_get_script():
    subprocess.call(['python', 'get.py'])
    # subprocess.call(['python3.10', 'get.py'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    return send_from_directory(os.getcwd(), 'final3_all.json', as_attachment=True)

@app.route('/next_run')
def next_run():
    job = scheduler.get_job('Scheduled Task')
    if job:
        next_run_time = job.next_run_time
        if next_run_time:
            now = datetime.now(timezone.utc)
            remaining_time = next_run_time - now
            return jsonify({
                'next_run_time': next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'remaining_time': str(remaining_time)
            })
    return jsonify({'error': 'Job not found'})

if __name__ == "__main__":
    # scheduler.add_job(id='Scheduled Task', func=run_get_script, trigger='interval', minutes=2)
    scheduler.add_job(id='Scheduled Task', func=run_get_script, trigger='interval', hours=12)
    scheduler.start()
    app.run(host='0.0.0.0', port=5000)
