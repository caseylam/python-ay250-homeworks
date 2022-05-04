import os
import pandas as pd
import numpy as np
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
import sqlite3
import query_alerts
from sqlalchemy import create_engine, text
from sqlalchemy.sql import select
import datetime

app = Flask(__name__)

# Write a function to view lightcurves (click and can go back to list, or go "next"), with an option to sort.
# Write a function to query and sort. 
# Option to save querys? 
# How to do version control? (As alert values update.) Have multiple databases? 
# Save in the database name the day it was created? 
# Have some function that knows the current year. If it was an old year, this is unnecessary.

engine = create_engine('sqlite:///microlensing.db')
conn = engine.connect()

@app.route('/', methods=['GET', 'POST'])
def start_page():
    """
    Homepage. Depending on whether there is a database or not,
    will either prompt you to upload, or will give you the 
    option to upload or query.
    """
    if engine.table_names() == []:
        return render_template('start_empty.html', web_download_to_db=url_for('web_download_to_db'))

    else:
        return render_template('start_filled.html', 
                               web_download_to_db=url_for('web_download_to_db'), 
                               query_db=url_for('query_db'),
                               dbs=engine.table_names())

@app.route('/update', methods=['GET', 'POST'])
def web_download_to_db():
    """
    FIXME: add an option to choose whether to keep or delete database.
    Don't redownload old years?
    """
    
    return render_template('download_data.html', start_page=url_for('start_page'))
    # return render_template('example.html')

@app.route('/handle_data', methods=['GET', 'POST'])
def handle_data():
    """
    FIXME: add an option to choose whether to keep or delete database.
    Actually, have radio buttons for this: Choose whether want lightcurves, data, system, and years.

    """
    duplicate_list = []
    update_list = []
    download_list = []

    this_year = str(datetime.date.today().year)
    
    keys = list(request.form.to_dict().keys())
    for ii, key in enumerate(keys):
        system, data, year = key.split('_')
        print(key)
        print(engine.table_names())
        
        if key in engine.table_names():
            if this_year == year:
                update_list.append(key)
            else:
                duplicate_list.append(key)
        else:
            download_list.append(key)

    for ii, key in enumerate(keys):
        system, data, year = key.split('_')
        if key in update_list + download_list:
            if system == 'KMTNet':
                if data == 'alerts':
                    query_alerts.get_kmtnet_alerts(year)
                else: # lightcurves
                    query_alerts.get_kmtnet_lightcurves(year)
            elif system == 'OGLE':
                if data == 'alerts':
                    query_alerts.get_ogle_alerts(year)
                else: # lightcurves
                    query_alerts.get_ogle_lightcurves(year)
            else: # MOA
                if data == 'alerts':
                    query_alerts.get_moa_alerts(year)
                else: # lightcurves
                    query_alerts.get_moa_lightcurves(year)
    print('update_list', update_list)
    print('duplicate_list', duplicate_list)
    print('download_list', download_list)
    # How to show processing? Googling "stream" and "dynamic" but I don't think that's what I want.
    return render_template('download_results.html', 
                            duplicate_list=duplicate_list,
                            update_list=update_list,
                            download_list=download_list,
                            web_download_to_db=url_for('web_download_to_db'), 
                            query_db=url_for('query_db'),
                            start_page=url_for('start_page'))

@app.route('/query', methods=['GET', 'POST'])
def query_db():
    """
    Provide the interface to query the database.
    """
    if request.method == 'POST':
        db_info = engine.execute(request.form['query']).fetchall()
        
        if len(db_info) == 0:
            return render_template('display_empty.html', 
                                   query_db=url_for('query_db'),
                                   start_page=url_for('start_page'))
        else:
            return render_template('display.html', len = len(db_info), 
                                   db_info = db_info, 
                                   start_page=url_for('start_page'))

    return render_template('query.html', start_page=url_for('start_page'), 
                            dbs=engine.table_names())

if __name__ == '__main__':
    app.run(port=8000, debug = True)
