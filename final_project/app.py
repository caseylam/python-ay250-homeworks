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
# Have way to download database.

engine = create_engine('sqlite:///microlensing.db')
conn = engine.connect()

@app.route('/', methods=['GET', 'POST'])
def start_page():
    """
    Homepage. Depending on whether there is a database or not,
    will either prompt you to download, or will give you the 
    option to download, query, or view MOA lightcurves.
    """
    if engine.table_names() == []:
        return render_template('start_empty.html', web_download_to_db=url_for('web_download_to_db'))

    else:
        return render_template('start_filled.html', 
                               dbs=engine.table_names(),
                               web_download_to_db=url_for('web_download_to_db'), 
                               query_db=url_for('query_db'),
                               browse_moa=url_for('browse_moa'))

@app.route('/update', methods=['GET', 'POST'])
def web_download_to_db():
    if request.method == 'POST':
        duplicate_list = []
        update_list = []
        download_list = []

        this_year = str(datetime.date.today().year)
        this_year = '2019'

        keys = list(request.form.to_dict().keys())
        for ii, key in enumerate(keys):
            system, data, year = key.split('_')
            print(key)

            if key in engine.table_names():
                if this_year == year:
                    update_list.append(key)
                    # FIXME: DELETE THE OLD TABLE FROM THE DATABASE.
                else:
                    duplicate_list.append(key)
            else:
                download_list.append(key)

        for ii, key in enumerate(keys):
            system, data, year = key.split('_')
            if key in update_list + download_list:
                if system == 'kmtnet':
                    if data == 'alerts':
                        query_alerts.get_kmtnet_alerts(year)
                    else: # lightcurves
                        query_alerts.get_kmtnet_lightcurves(year)
                elif system == 'ogle':
                    if data == 'alerts':
                        query_alerts.get_ogle_alerts(year)
                    else: # lightcurves
                        query_alerts.get_ogle_lightcurves(year)
                else: # MOA
                    if data == 'alerts':
                        query_alerts.get_moa_alerts(year)
                    else: # lightcurves
                        query_alerts.get_moa_lightcurves(year)

        # How to show processing? Googling "stream" and "dynamic" but I don't think that's what I want.
        return render_template('download_results.html', 
                                duplicate_list=duplicate_list,
                                update_list=update_list,
                                download_list=download_list,
                                web_download_to_db=url_for('web_download_to_db'), 
                                query_db=url_for('query_db'),
                                start_page=url_for('start_page'))
    
    return render_template('download_data.html', start_page=url_for('start_page'))

@app.route('/query', methods=['GET', 'POST'])
def query_db():
    """
    Provide the interface to query the database.
    """
    if request.method == 'POST':
        query_str = request.form['query']
        db_info = engine.execute(query_str).fetchall()
        
        if len(db_info) == 0:
            return render_template('display_empty.html', 
                                   query_str=query_str,
                                   query_db=url_for('query_db'),
                                   start_page=url_for('start_page'))
        else:
            return render_template('display.html', 
                                   query_str=query_str,
                                   len = len(db_info), 
                                   db_info = db_info, 
                                   start_page=url_for('start_page'))

    return render_template('query.html', 
                           web_download_to_db=url_for('web_download_to_db'),
                           start_page=url_for('start_page'), 
                           dbs=engine.table_names())

# @app.route('/browse_moa', methods=['GET', 'POST'])
# def browse_moa():
#     dbs=engine.table_names()
#     moa_lcs = [dbname for dbname in dbs if 'moa_lightcurves' in dbname]
#     if moa_lcs == []:
#         return render_template('moa_lightcurves_empty.html',
#                                 web_download_to_db=url_for('web_download_to_db'),
#                                 start_page=url_for('start_page'))
#     else:
#         pass
    
@app.route('/plot/<moa_alert_name>')
def plot_moa(moa_alert_name):
    # Check if variable exists first.
    # https://stackoverflow.com/questions/843277/how-do-i-check-if-a-variable-exists
    
    n_lc = len(moa_names)
    ii = moa_names.index(moa_alert_name)
    return render_template('test_number.html', 
                           home=url_for('start_page'),
                           ii=ii,
                            next_page=url_for('plot_moa', moa_alert_name=moa_names[ii+1]), 
                            prev_page=url_for('plot_moa', moa_alert_name=moa_names[ii-1]), 
                            qmax=n_lc + 1,
                          moa_names=moa_names)
    
@app.route('/browse_moa', methods=['GET', 'POST'])
def browse_moa():
    if request.method == 'POST':
        query_str = request.form['query']
        db_info = engine.execute('SELECT DISTINCT alert_name ' + query_str).fetchall()
        
        if len(db_info) == 0:
            return 'Nothing' # Make this a page.
        else:
            n_lc = len(db_info) + 1
        
            # Make the names of the moa lightcurves here a global function...
            # Is there a better way to do this??????
            global moa_names
            moa_names = [str(mname).strip(',()\'') for mname in db_info]
            return render_template('moa_lightcurves_list.html', 
                                    alert_names=moa_names)
        
    dbs=engine.table_names()
    moa_lcs = [dbname for dbname in dbs if 'moa_lightcurves' in dbname]
    if moa_lcs == []:
        return render_template('moa_lightcurves_list.html',
                                plot_moa=url_for('web_download_to_db'),
                                start_page=url_for('start_page'))
    else:
        return render_template('moa_lightcurves_exist.html',
                                moa_lcs=moa_lcs,
                                web_download_to_db=url_for('web_download_to_db'),
                                start_page=url_for('start_page'))

if __name__ == '__main__':
    app.run(port=8000, debug = True)
