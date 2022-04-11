# https://flask.palletsprojects.com/en/2.1.x/patterns/fileuploads/
import os
import pandas as pd
import numpy as np
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
from pybtex.database import parse_file 

"""
Useful examples: https://stackoverflow.com/questions/62004957/crating-an-if-statement-for-different-html-option-in-flask-python
"""

UPLOAD_FOLDER = '/home/jovyan/python-ay250-homeworks/hw_7/bibuploads'
ALLOWED_EXTENSIONS = {'bib'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def start_page():
    if os.listdir(UPLOAD_FOLDER) == []:
        return render_template('start_empty.html', upload_file=url_for('upload_file'))

    else:
        return render_template('start_filled.html', 
                               upload_file=url_for('upload_file'), query_db=url_for('query_db'))

@app.route('/update', methods=['GET', 'POST'])
def upload_file():
    # FIXME: figure out how to save the collection name.
    # Also need to figure out these if statements and error stuff.
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #return redirect(url_for('download_file', name=filename))
            return redirect(url_for('start_page'))
    return render_template('upload_file.html')

@app.route('/query', methods=['GET', 'POST'])
def query_db():
    return

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

if __name__ == '__main__':
    app.run(port=8000, debug = True)
