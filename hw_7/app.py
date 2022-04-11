# https://flask.palletsprojects.com/en/2.1.x/patterns/fileuploads/
import os
import pandas as pd
import numpy as np
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
from pybtex.database import parse_file 
import sqlite3

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

def parse_bib_to_df(bibfile, collection_name):
    """
    Parse a bibtex file into a pandas dataframe.
    Keeps only the tag, author, journal, volume, pages, year,
    (For easy insertion into an SQL database later.)
    
    bibfile : a .bib file
    collection_name : string
    """
    bib_data = parse_file(bibfile, "bibtex")

    tag_list = []
    author_list = []
    journal_list = []
    volume_list = []
    pages_list = []
    year_list = []
    title_list = []
    collection_list = []

    for tag in list(bib_data.entries.keys()):
        if 'Author' in bib_data.entries[tag].persons:
            for author_name in list(bib_data.entries[tag].persons['Author']):
                author = author_name.last_names[0][1:-1]
                if 'journal' in bib_data.entries[tag].fields._dict:
                    journal = bib_data.entries[tag].fields._dict['journal'][1:]
                else:
                    journal = np.nan

                if 'volume' in bib_data.entries[tag].fields._dict: 
                    volume = int(bib_data.entries[tag].fields._dict['volume'])
                else:
                    journal = np.nan

                if 'pages' in bib_data.entries[tag].fields._dict: 
                    pages = bib_data.entries[tag].fields._dict['pages']
                else:
                    journal = np.nan

                if 'year' in bib_data.entries[tag].fields._dict: 
                    year = int(bib_data.entries[tag].fields._dict['year'])
                else:
                    journal = np.nan

                if 'title' in bib_data.entries[tag].fields._dict: 
                    title = bib_data.entries[tag].fields._dict['title'][1:-1]
                else:
                    journal = np.nan

                tag_list.append(tag)
                author_list.append(author)
                journal_list.append(journal)
                volume_list.append(volume)
                pages_list.append(pages)
                year_list.append(year)
                title_list.append(title)
                collection_list.append(collection_name)

    df = pd.DataFrame({'tag': tag_list, 'author': author_list,
                        'journal' : journal_list, 'volume' : volume_list,
                        'pages' : pages_list, 'year' : year_list,
                        'title' : title_list, 'collection' : collection_list})
    
    return df

def df_to_sql(df):
    # FIXME: SAVE THIS TO A PARTICULAR PLACE??
    connection = sqlite3.connect("bibliography.db")

    cursor = connection.cursor()

    sql_cmd = """CREATE TABLE bibliography 
                (iid INTEGER  NOT NULL  PRIMARY KEY  AUTOINCREMENT DEFAULT 0, 
                tag TEXT, 
                author TEXT, 
                journal TEXT, 
                volume FLOAT, 
                pages TEXT,
                year FLOAT,
                title TEXT,
                collection TEXT)"""

    cursor.execute(sql_cmd)
    connection.commit()
    
    df = df.where(pd.notnull(df), None)
    for ii, row in df.iterrows():
        iparams = (row['tag'], row['author'], row['journal'], row['volume'], 
                   row['pages'], row['year'], row['title'], row['collection'])
        sql_cmd = """INSERT INTO bibliography
                    (tag, author, journal, volume, pages, year, title, collection)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

        cursor.execute(sql_cmd, iparams)
    connection.commit()
    return

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
            collection_name = request.form['collname']
            filename = secure_filename(file.filename)
            bibfile = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(bibfile)
            
            # Save bib into dataframe
            bibdf = parse_bib_to_df(bibfile, collection_name)
            df_to_sql(bibdf)
            
            return redirect(url_for('start_page'))
    return render_template('upload_file.html')

@app.route('/results')
def display_query_results(db_info):
    """
    db_info : the result of the SQL query.
    """
    return render_template('display.html', len = len(db_info), db_info = db_info)
    
@app.route('/query', methods=['GET', 'POST'])
def query_db():
    if request.method == 'POST':
        connection = sqlite3.connect("bibliography.db")
        cursor = connection.cursor()
        sql_cmd = request.form['query']
        cursor.execute(sql_cmd)

        db_info = cursor.fetchall()
        print(db_info)
        
        return render_template('display.html', len = len(db_info), db_info = db_info)

    return render_template('query.html')

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

if __name__ == '__main__':
    app.run(port=8000, debug = True)
