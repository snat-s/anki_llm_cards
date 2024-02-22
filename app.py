from flask import Flask, render_template, request, send_file, redirect, url_for
from generate_anki import generate_anki
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER


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
        if not os.path.exists('uploads'):
            os.makedirs('uploads')

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # process
        processed_content = generate_anki(file_path, num_cards)
        return send_file(processed_content, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
