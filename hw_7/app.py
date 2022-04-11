# https://flask.palletsprojects.com/en/2.1.x/patterns/fileuploads/
import os
import pandas as pd
import numpy as np
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from pybtex.database import parse_file 

"""
EXAMPLE FROM STACKEXCHANGE:

def submit():
    if request.method == 'POST':
        select = request.form.get('articles')
        if select == "Gaurdian":
            return redirect(url_for("X_route"))
        if select == "BBC":
            return redirect(url_for("Y_route))
    return render_template('scraped.html', s1=summary, s2=summary2)

@app.route("/X_route")
def X_route():
    return render_template("X.html")

@app.route("/Y_route")
def Y_route():
    return render_template("Y.html")
"""

UPLOAD_FOLDER = '/home/jovyan/python-ay250-homeworks/hw_7/static'
ALLOWED_EXTENSIONS = {'bib'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def start_page():
    if os.listdir(UPLOAD_FOLDER) == []:
        return """
        <!doctype html>
        <html>
        <body>
        <p>No collections exist. Cannot perform query.</p>
        <p><a href="{upload_file}">Upload a collection here.</a></p>
        </body>
        </html>
        """.format(upload_file=url_for('upload_file'))
    else:
        return """
        <!doctype html>
        <html>
        <body>
            <p>At least one collection exists.</p>
            <p><a href="{upload_file}">Add another collection here.</a></p>
            <p><a href="{query_db}">Query the collection here.</a></p>
        </body>
        </html>
        """.format(upload_file=url_for('upload_file'), query_db=url_for('query_db'))
        
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
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
    Collection name:
      <input type=text name=collname>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

@app.route('/query', methods=['GET', 'POST'])
def query_db():
    return

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

if __name__ == '__main__':
    app.run(port=8000, debug = True)
