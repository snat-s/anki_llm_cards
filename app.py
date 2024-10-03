from flask import Flask, render_template, request, send_file, url_for, jsonify, redirect
from celery import Celery
from generate_anki import generate_anki
from io import BytesIO
import os

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def generate_anki_task(file_content, num_cards):
    return generate_anki(file_content, num_cards, is_file=False).getvalue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', message='No file found')
    
    file = request.files['file']
    num_cards = int(request.form.get('numCards'))
    
    if file.filename == '':
        return render_template('index.html', message='No selected file')
    
    if file:
        file_content = file.read().decode('utf-8')
        task = generate_anki_task.delay(file_content, num_cards)
        return redirect(url_for('processing', task_id=task.id))

@app.route('/processing/<task_id>')
def processing(task_id):
    return render_template('processing.html', task_id=task_id)

@app.route('/status/<task_id>')
def task_status(task_id):
    task = generate_anki_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is being processed...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': 'Task completed successfully.'
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)
        }
    return jsonify(response)

@app.route('/download/<task_id>')
def download_file(task_id):
    task = generate_anki_task.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        mem = BytesIO(task.result.encode('utf-8'))
        return send_file(
            mem,
            as_attachment=True,
            download_name='anki_cards.csv',
            mimetype='text/csv'
        )
    else:
        return "Task not completed yet."

if __name__ == '__main__':
    app.run(debug=True)
