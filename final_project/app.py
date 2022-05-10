import os
import pandas as pd
import numpy as np
from flask import Flask, Response, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
import sqlite3
# import query_alerts
from sqlalchemy import create_engine, text
from sqlalchemy.sql import select
import datetime
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import base64
import numexpr as ne
from flask import make_response

app = Flask(__name__)

# The database.
engine = create_engine('sqlite:///microlensing.db')

# Check if tables exists yet, if not, then populate?

@app.route('/', methods=['GET', 'POST'])
def start_page():
    """
    Homepage. Depending on whether there is a database or not,
    will either prompt you to download, or will give you the 
    option to download, query, or view MOA lightcurves.
    """
#     if engine.table_names() == []:
#         return render_template('start_empty.html', 
#                                web_download_to_db=url_for('web_download_to_db'))

#     else:
#         return render_template('start_filled.html', 
#                                dbs=engine.table_names(),
#                                web_download_to_db=url_for('web_download_to_db'), 
#                                query_db=url_for('query_db'),
#                                browse_moa=url_for('browse_moa'))
    return render_template('start.html', 
                           dbs=engine.table_names(),
                           query_db=url_for('query_db'),
                           browse_moa=url_for('browse_moa'))

# @app.route('/update', methods=['GET', 'POST'])
def web_download_to_db():
    """
    Page that lets you pick what data to download.
    """
    if request.method == 'POST':
        
        # We divide up datasets into things that have:
        # 1) already been downloaded (duplicate)
        # 2) already been downloaded, but are
        #    from the current year of alerts (update)
        # 3) not yet been downloaded (download)
        duplicate_list = []
        update_list = []
        download_list = []

        this_year = str(datetime.date.today().year)
        this_year = '2019' # FIXME TEMPORARY FOR DEBUGGING.

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

        # If dataset is in download or update list, then download
        # the right combo of KMTNet/OGLE/MOA lightcurves/alerts.
        for ii, key in enumerate(keys):
            system, data, year = key.split('_')
            if key in update_list + download_list:
                if system == 'kmtnet':
                    if data == 'alerts':
                        query_alerts.get_kmtnet_alerts(year)
                    else: 
                        query_alerts.get_kmtnet_lightcurves(year)
                elif system == 'ogle':
                    if data == 'alerts':
                        query_alerts.get_ogle_alerts(year)
                    else: 
                        query_alerts.get_ogle_lightcurves(year)
                elif system == 'moa': 
                    if data == 'alerts':
                        query_alerts.get_moa_alerts(year)
                    else:
                        query_alerts.get_moa_lightcurves(year)
                else:
                    raise Exception('That is not a valid survey name!')

        # How to show processing? Googling "stream" and "dynamic" but I don't think that's what I want.
        return render_template('download_results.html', 
                                duplicate_list=duplicate_list,
                                update_list=update_list,
                                download_list=download_list,
                                web_download_to_db=url_for('web_download_to_db'), 
                                query_db=url_for('query_db'),
                                start_page=url_for('start_page'))
    
    return render_template('download_data.html', start_page=url_for('start_page'))

@app.route('/download_csv/<query_str>', methods=['GET', 'POST'])
def download_csv(query_str):
    """
    Download the result of the SQL query as a CSV file.
    Note: can read the result with pandas read_csv and it will
    give you the column names.
    """
    with engine.connect() as conn:
        df = pd.read_sql(query_str, conn)
        print(df.columns)
    resp = make_response(df.to_csv())
    resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
    resp.headers["Content-Type"] = "text/csv"
    
    return resp

@app.route('/query', methods=['GET', 'POST'])
def query_db():
    """
    Page that provides the interface to query the database.
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
                                   start_page=url_for('start_page'),
                                   download_csv=url_for('download_csv', query_str=query_str))
        
    return render_template('query.html', 
#                           web_download_to_db=url_for('web_download_to_db'),
                           start_page=url_for('start_page'), 
                           alert_column_names=url_for('alert_column_names'),
                           dbs=engine.table_names())

@app.route('/alert_column_names', methods=['GET', 'POST'])
def alert_column_names():
    """
    Page that lists all the alert column names.
    """
    return render_template('alert_help.html', 
                           query_db=url_for('query_db'),
                           start_page=url_for('start_page'))

def create_figure(time, mag, mag_err, moa_alert_name):
    """
    Plot MOA lightcurve.
    
    Parameters
    ----------
    time : array-like
        Time (HJD - 2450000)
        
    mag : array-like
        I-band magnitude
    
    mag_err : array-like
        Magnitude uncertainties
        
    moa_alert_name : string
        Name of the MOA alert
        
    Return
    ------
    pngImageB64String : FIXME what is this really?
        This format was chosen so you can pass it into <img src = ...
    """
    #####
    # Figure out limits for plotting the y-axis (magnitude).
    ####
    # MOA alert data is very noisy. We will take the minimum and maximum
    # magnitude range of the observations. But we only use the observations
    # that have error bars in 95% or lower. (Could tweak, I arbitrarily  chose
    # this number to cut out as much junky stuff as possible, but hopefully not 
    # actual data or the peak of the lightcurve.)
    big_err = np.quantile(mag_err, 0.95)
    idx = np.where(mag_err < big_err)[0]
    
    # Get our min and max magnitudes from the less noisy data.
    ymin = np.min(mag[idx])
    ymax = np.max(mag[idx])
    
    # Change opacity of points depending how many there are.
    npoints = len(time)
    if (npoints <= 5000):
        alpha=0.6
    elif (npoints <= 10000) & (npoints > 5000):
        alpha=0.4
    elif (npoints <= 30000) & (npoints > 10000):
        alpha=0.2
    elif (npoints <= 50000) & (npoints > 30000):
        alpha = 0.05
    else:
        alpha=0.01
    
    # Set up the figure and plot the lightcurve.
    fig = Figure(figsize=(12,6))
    axis = fig.add_subplot(1, 1, 1)
    axis.set_ylim(ymin - 0.2, ymax + 0.2)
    axis.invert_yaxis()
    axis.set_xlabel('HJD - 2450000')
    axis.set_ylabel('I mag')
    axis.errorbar(time, mag, yerr=mag_err, ls='none', marker='.', alpha=alpha, color='k')
    axis.set_title(moa_alert_name)
    
    # Fancy saving stuff: https://stackoverflow.com/questions/61398636/python-flask-matplotlib
    pngImage = io.BytesIO()
    FigureCanvas(fig).print_png(pngImage)
    
    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

    return pngImageB64String

@app.route('/fig/<moa_alert_name>')
def plot_moa(moa_alert_name):
    """
    Page that shows the MOA lightcurve in magnitude space.
    """
    # Check if variable exists first.
    # https://stackoverflow.com/questions/843277/how-do-i-check-if-a-variable-exists
    
    # Year string.
    YY = moa_alert_name[2:4]
    
    # Grab the MOA hjd, mag, mag_err corresponding to the alert name.
    query_str = 'SELECT hjd, mag, mag_err FROM moa_lightcurves_20' + YY + \
                ' WHERE alert_name = "' + moa_alert_name + '"' 
    
    # The *1 is just a dumb trick to turn it into an integer.
    year = ne.evaluate(YY) * 1 
    hjd_jan_00 = 1154
    
    start_date = hjd_jan_00 + 365.25 * (year)
    end_date = hjd_jan_00 + 365.25 * (year + 2) # This gives us data through that year's alert season.
    # Why is it year and year+2? Should be year -1 and year+1?
    
    # Get hjd, mag, mag_err from the query.
    db_info = engine.execute(query_str).fetchall()
    time = np.array([info[0] for info in db_info])
    mag = np.array([info[1] for info in db_info])
    mag_err = np.array([info[2] for info in db_info])
    
    # Now only keep things from the year of and before.
    keep_idx = np.where((time < end_date) & (time > start_date))[0]
    
    # Make the plot.
    fig = create_figure(time[keep_idx], mag[keep_idx], mag_err[keep_idx], moa_alert_name)
    
    # Figure out which entry in the list this is so we know which template to use below.
    # Tried to get all those if statement below into the template but couldn't get it quite to work...
    n_lc = len(moa_names)
    ii = moa_names.index(moa_alert_name)

    # Catch edge case with only one result.
    if n_lc == 1:
        return render_template('show_moa_lc_one.html', 
                                home=url_for('start_page'),
                                image=fig)
    # First page.
    if ii == 0:
        return render_template('show_moa_lc_first.html', 
                                home=url_for('start_page'),
                                next_page=url_for('plot_moa', moa_alert_name=moa_names[ii+1]), 
                                moa_names=moa_names,
                                image=fig)
    # Last page.
    elif ii == n_lc - 1:
        return render_template('show_moa_lc_last.html', 
                                home=url_for('start_page'),
                                prev_page=url_for('plot_moa', moa_alert_name=moa_names[ii-1]), 
                                moa_names=moa_names,
                                image=fig)
    # Middle pages.
    else:
        return render_template('show_moa_lc.html', 
                                home=url_for('start_page'),
                                next_page=url_for('plot_moa', moa_alert_name=moa_names[ii+1]), 
                                prev_page=url_for('plot_moa', moa_alert_name=moa_names[ii-1]), 
                                qmax=n_lc-1,
                                moa_names=moa_names,
                                image=fig)
    
@app.route('/browse_moa', methods=['GET', 'POST'])
def browse_moa():
    """
    Page that lets you pick which MOA lightcurves you want to plot in magnitude space.
    """
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
                                    alert_names=moa_names,
                                    start_page=url_for('start_page'),
                                    browse_moa=url_for('browse_moa'))
        
    dbs=engine.table_names()
    # FIXME: WILL HAVE TO CHANGE THIS.
    moa_lcs = [dbname for dbname in dbs if 'moa_lightcurves' in dbname]
#     if moa_lcs == []:
#         return render_template('moa_lightcurves_list.html',
#                                 plot_moa=url_for('web_download_to_db'),
#                                 start_page=url_for('start_page'))
#     else:
#         return render_template('moa_lightcurves_exist.html',
#                                 moa_lcs=moa_lcs,
#                                 web_download_to_db=url_for('web_download_to_db'),
#                                 start_page=url_for('start_page'))
    return render_template('moa_lightcurves.html',
                            moa_lcs=moa_lcs,
                            start_page=url_for('start_page'))


if __name__ == '__main__':
    app.run(port=8000, debug = True)
