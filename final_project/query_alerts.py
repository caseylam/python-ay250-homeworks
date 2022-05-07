
import ftplib
from sqlalchemy import create_engine, text
from sqlalchemy.sql import select
from bs4 import BeautifulSoup
import numpy as np 
from io import BytesIO
import pandas as pd
import time 
from urllib.request import urlopen
import numexpr as ne
import requests
import time
import multiprocessing as mp
from itertools import repeat

# Setting up database stuff with SQLAlchemy.
engine = create_engine('sqlite:///microlensing.db')
conn = engine.connect()

def get_moa_lightcurves(year):
    """
    Function that grabs MOA lightcurves from the alert pages 
    and writes them to a table in the database.
    
    Note that we don't care about the delta flux photometry...
    what we really care about is the photometry in magnitudes.
    This function takes the reported calibration values from
    the MOA webpage, and converts the delta flux and flux error
    measurements into magnitude and magnitude errors.

    Parameters
    ----------
    year : int
        Year of the MOA alerts you want. 
        Valid choices are 2016 - 2022, inclusive.
        
    Outputs
    -------
    sqlite table called moa_<YYYY> in microlensing.db
    Columns are hjd (HJD - 245000), mag, mag_err, alert_name.
    """
    # The delta flux measurements sometimes yield negative fluxes
    # after calibration. Ignore warnings so we don't have to deal
    # with the log10 complaining during the magnitude conversion.
    import warnings
    warnings.filterwarnings("ignore")

    # Go to the MOA alerts site and scrape the page.
    year = str(year)
    url = "http://www.massey.ac.nz/~iabond/moa/alert" + year + "/alert.php"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")

    # Get a list of all the bulge microlensing alert directories.
    links = soup.find_all('a', href=True)
    alert_dirs = []
    for ii, link in enumerate(links):
        if 'BLG' in link.text:
            alert_dirs.append(links[ii]['href'])

    t0 = time.time() 
    # Go to the page for each bulge microlensing alert.
    for nn, alert_dir in enumerate(alert_dirs):
        # Scrape the page.
        url = "http://www.massey.ac.nz/~iabond/moa/alert" + year + "/" + alert_dir
        response = urlopen(url)
        html = response.read()
        response.close()
        soup = BeautifulSoup(html,"html.parser")

        # Get the magnitude and flux offsets, so we can convert
        # from delta flux to a magnitude.
        foo = soup.find('b').next_sibling
        moff = foo.split('=')[1].split('-')[0].strip(' ')
        bah = soup.find('sub').next_sibling
        foff = bah.split('+')[1].split(')')[0].strip(' ')

        # Convert those offsets from strings into floats
        m = ne.evaluate(moff)
        f = ne.evaluate(foff)

        # Grab the .dat file containing the photometry data into a pandas dataframe.
        url = "https://www.massey.ac.nz/~iabond/moa/alert" + year + "/fetchtxt.php?path=moa/ephot/phot-" + \
                alert_dir.strip('display.php?id=') + ".dat"
        bytes_data = requests.get(url).content
        df = pd.read_csv(BytesIO(bytes_data), 
                         delim_whitespace=True, skiprows=11, skipfooter=1, header=None, engine='python', 
                         names=['hjd', 'delta_flux', 'flux_err', 'foo1', 'foo2', 'foo3', 'foo4', 'foo5'])

        # Add columns for magnitude and magnitude error, using the conversion
        # values we just figured out.
        df['mag'] = m - 2.5*np.log10(df['delta_flux'] + f)
        df['mag_err'] = 1.09 * df['flux_err']/(df['delta_flux'] + f)
        
        # Add a column for the alert name (of the form MBYYNNN, YY=year, NNN=alert number)
        df['alert_name'] = 'MB' + year[2:] + str(nn + 1).zfill(3)  # need to make sure this always works.
        
        # Write HJD as HJD - 2450000 to match OGLE and KMTNet (less cumbersome digits)
        df['hjd'] -= 2450000

        # Get rid of all the nans which crop up during the conversion from delta flux to magnitude.
        df.dropna(axis='index', how='any', inplace=True)

        # Write out the HJD, mag, mag_err, and alert_names data into the table. 
        cols = ['hjd', 'mag', 'mag_err', 'alert_name']
        df[cols].to_sql(con=engine, schema=None, name="moa_lightcurves_" + year, if_exists="append", index=False)
    t1 = time.time() 
    
    print('Took {0:.2f} seconds'.format(t1-t0))
    
def get_ogle_lightcurves(year):
    """
    Function that grabs OGLE lightcurves from the alert website 
    and writes them to a table in the database.

    Parameters
    ----------
    year : int
        Year of the MOA alerts you want. 
        Valid choices are 2011 - 2029, inclusive.
        
    Outputs
    -------
    sqlite table called ogle_<YYYY> in microlensing.db
    Columns are hjd (HJD - 245000), mag, mag_err, alert_name.
    """
    # Go to the OGLE alert site and get the data with FTP.
    year = str(year)
    ftp = ftplib.FTP("ftp.astrouw.edu.pl")
    ftp.login()
    ftp.cwd("ogle/ogle4/ews/" + year + "/")
    
    # Figure out how many objects there are by counting the number of .tar.gz files 
    # in the directory (each .tar.gz file corresponds to an alert)
    nobj = sum('.tar.gz' in x for x in ftp.nlst())
 
    t0 = time.time() 
    for nn in np.arange(start=1, stop=nobj+1, step=1):
        # Grab the photometry for each alert.
        ftp.cwd("blg-" + str(nn).zfill(4))
        
        flo = BytesIO()
        ftp.retrbinary('RETR phot.dat', flo.write)
        flo.seek(0)
        df = pd.read_fwf(flo, header=0, 
                         names=['hjd', 'mag', 'mag_err', 'see', 'sky'], 
                         widths=[14, 7, 6, 5, 8])

        # Add a column for the alert name (of the form OBYYNNNN, YY=year, NNN=alert number)
        df['alert_name'] = 'OB' + year[2:] + str(nn + 1).zfill(4) 

        # Write out the HJD, mag, mag_err, and alert_names data into the table. 
        cols = ['hjd', 'mag', 'mag_err', 'alert_name']
        df[cols].to_sql(con=engine, schema=None, name="ogle_lightcurves_" + year, if_exists="append", index=False)

        ftp.cwd("../")
    t1 = time.time() 
    ftp.close()
    
    print('Took {0:.2f} seconds'.format(t1-t0))
    
def get_kmtnet_lightcurves(year):
    """
    Function that grabs KMTNet lightcurves from the alert pages 
    and writes them to a table in the database.

    Parameters
    ----------
    year : int
        Year of the KMTNet alerts you want. 
        Valid choices are 2016 - 2022, inclusive.
        
    Outputs
    -------
    sqlite table called kmtnet_<YYYY> in microlensing.db
    Columns are hjd (HJD - 245000), mag, mag_err, alert_name, and lightcurve (the pysis name).
    """
    # Figure out how many objects there are by counting how many columns
    # there are on the alert page.
    year = str(year)
    url = "https://kmtnet.kasi.re.kr/~ulens/event/" + year + "/"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")
    nobj = len(soup.find_all('td')[0::15][1:])
    
    t0 = time.time()
    # Go to the KMTNet alerts site and scrape the page for each alert.
    for nn in np.arange(start=1, stop=nobj+1, step=1):
        url = "https://kmtnet.kasi.re.kr/~ulens/event/" + year + "/view.php?event=KMT-" + year + \
                "-BLG-" + str(nn).zfill(4)
        response = urlopen(url)
        html = response.read()
        response.close()
        soup = BeautifulSoup(html,"html.parser")

        # Get the names of all the different lightcurve files (pysis names).
        links = soup.find_all('a', href=True)
        pysis_names = links[3].get_text(separator=',').split(',')[:-2]
        
        # Note, we are only keeping I-band lightcurves (V-band ones are not useful). 
        for pysis_name in pysis_names:
            if '_I.pysis' in pysis_name:
                # Grab the photometry for each alert's I-band lightcurve data into a pands dataframe.
                url = "https://kmtnet.kasi.re.kr/~ulens/event/" + year + "/data/KB" + \
                        year[2:] + str(nn).zfill(4) + "/pysis/" + pysis_name
                bytes_data = requests.get(url).content
                df = pd.read_csv(BytesIO(bytes_data), 
                                 delim_whitespace=True, skiprows=1, header=None, 
                                 names=['hjd', 'Delta_flux', 'flux_err', 'mag', 'mag_err', 'fwhm', 'sky', 'secz'])

                # Add columns for the alert name (of the form KBYYNNNN, YY=year, NNNN=alert number)
                # and the name of the lightcurve's pysis file.
                df['alert_name'] = 'KB' + year[2:] + str(nn).zfill(4) 
                df['lightcurve'] = pysis_name

                # Write out the HJD, mag, mag_err, lightcurve, and alert_name data into the table.
                cols = ['hjd', 'mag', 'mag_err', 'lightcurve', 'alert_name']
                df[cols].to_sql(con=engine, schema=None, name="kmtnet_lightcurves_" + year, 
                                if_exists="append", index=False)
    t1 = time.time()             
    
    print('Took {0:.2f} seconds'.format(t1-t0))

def get_moa_alerts(year):
    """
    **********************
    !!!!!!! FIXME !!!!!!!!
    **********************
    Function that grabs OGLE alerts and writes the fit
    tE and Ibase parameters to a table in the database.
    
    Parameters
    ----------
    year : int
        Year of the OGLE alerts you want.
        Valid choices are 2001 - 2019, inclusive.
        
    Outputs
    -------
    sqlite table called ogle_alerts_<YYYY> in microlensing.db
    Columns are alert_name, tE, Ibase, alert_url.
    """    
    def moa_str_to_float(list_in):
        try:
            return float(ne.evaluate(list_in))
        except:
            return np.nan
    
    # Go to the MOA alerts site and scrape the page.
    year = str(year)
    url = "http://www.massey.ac.nz/~iabond/moa/alert" + year + "/alert.php"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")

    # Get a list of all the bulge microlensing alert directories.
    links = soup.find_all('a', href=True)
    alert_dirs = []
    for ii, link in enumerate(links):
        if 'BLG' in link.text:
            alert_dirs.append(links[ii]['href'])
        
    # Values we are going to populate
    npages = len(alert_dirs)
    RA_arr = np.zeros(npages)
    Dec_arr = np.zeros(npages)
    tmax_arr = np.zeros(npages)
    tmax_e_arr = np.zeros(npages)
    tE_arr = np.zeros(npages)
    tE_e_arr = np.zeros(npages) 
    u0_arr = np.zeros(npages) 
    u0_e_arr = np.zeros(npages) 
    Ibase_arr = np.zeros(npages) 
    Ibase_e_arr = np.zeros(npages) 

    _t0 = time.time()
    # Go to the page for each bulge microlensing alert.
    for nn, alert_dir in enumerate(alert_dirs):
        # Scrape the page.
        url = "http://www.massey.ac.nz/~iabond/moa/alert" + year + "/" + alert_dir
        response = urlopen(url)
        html = response.read()
        response.close()
        soup = BeautifulSoup(html,"html.parser")
        
        meta = soup.find('div', id="metadata").text
        ra = meta.split('RA:')[1].split('Dec:')[0]
        dec = meta.split('RA:')[1].split('Dec:')[1].split('Current')[0]
        
        tmax_str = soup.find('div', id="lastphot").text.split('<td>=<td align=right>')[1]
        tmax = tmax_str.split()[1]
        tmax_e = tmax_str.split('<td>')[2].split()[0]

        tE_str = soup.find('div', id="lastphot").text.split('<td>=<td align=right>')[2]
        tE = tE_str.split()[0]
        tE_e = tE_str.split('<td>')[2].split()[0]

        u0_str = soup.find('div', id="lastphot").text.split('<td>=<td align=right>')[3]
        u0 = u0_str.split()[0]
        u0_e = u0_str.split('<td>')[2].split()[0].split('<')[0]

        Ibase_str = soup.find('div', id="lastphot").text.split('<td>=<td align=right>')[4]
        Ibase = Ibase_str.split()[0]
        Ibase_e = Ibase_str.split('<td>')[2].split()[0].split('<')[0]
        
        RA_arr[nn] = ra
        Dec_arr[nn] = dec
        tmax_arr[nn] = moa_str_to_float(t0)
        tmax_e_arr[nn] = moa_str_to_float(t0e)
        tE_arr[nn] =  moa_str_to_float(tE)
        tE_e_arr[nn] =  moa_str_to_float(tEe)
        u0_arr[nn] =  moa_str_to_float(u0)
        u0_e_arr[nn] =  moa_str_to_float(u0e)
        Ibase_arr[nn] =  moa_str_to_float(Ibase)
        Ibase_e_arr[nn] =  moa_str_to_float(Ibasee)
            
    # Put it all into a dataframe and write out to the database.
    df = pd.DataFrame(list(zip(RA_arr, Dec_arr, tmax_arr, tmax_e_arr, 
                               tE_arr, tE_e_arr, u0_arr, u0_e_arr, 
                               Ibase_arr, Ibase_e_arr)),
                     columns =['RA_arr', 'Dec_arr', 'tmax_arr', 'tmax_e_arr', 
                               'tE_arr', 'tE_e_arr', 'u0_arr', 'u0_e_arr', 
                               'Ibase_arr', 'Ibase_e_arr'])

    df.to_sql(con=engine, schema=None, name="moa_alerts_" + year, if_exists="replace", index=False)
    
    _t1 = time.time()
    print('Took {0:.2f} seconds'.format(_t1-_t0))

def get_ogle_params(year, nn):    
    url = "https://ogle.astrouw.edu.pl/ogle4/ews/" + year + "/blg-" + str(nn+1).zfill(4) + ".html"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")
    header_list = soup.find_all('table')[1].find('td').text.split()
    param_list = soup.find_all('table')[2].find('td').text.split()

    RA = header_list[7]
    Dec = header_list[10]
    Tmax = ogle_str_to_float(param_list, 1)
    Tmax_e = ogle_str_to_float(param_list, 3)
    tau =  ogle_str_to_float(param_list, 7)
    tau_e =  ogle_str_to_float(param_list, 9)
    Umin =  ogle_str_to_float(param_list, 11)
    Umin_e =  ogle_str_to_float(param_list, 13)
    Amax =  ogle_str_to_float(param_list, 15)
    Amax_e =  ogle_str_to_float(param_list, 17)
    Dmag =  ogle_str_to_float(param_list, 19)
    Dmag_e =  ogle_str_to_float(param_list, 21)
    fbl =  ogle_str_to_float(param_list, 23)
    fbl_e =  ogle_str_to_float(param_list, 25)
    Ibl =  ogle_str_to_float(param_list, 27)
    Ibl_e =  ogle_str_to_float(param_list, 29)
    I0 = ogle_str_to_float(param_list, 31)
    I0_e =  ogle_str_to_float(param_list, 33)

    return RA, Dec, Tmax, Tmax_e, tau, tau_e, Umin, Umin_e, \
            Amax, Amax_e, Dmag, Dmag_e, fbl, fbl_e, Ibl, Ibl_e, I0, I0_e
    
def ogle_str_to_float(list_in, idx):
    try:
        return float(ne.evaluate(list_in[idx]))
    except:
        return np.nan
        
def get_ogle_alerts(year):
    """
    **********************
    !!!!!!! FIXME !!!!!!!!
    **********************
    Function that grabs OGLE alerts and writes the fit
    tE and Ibase parameters to a table in the database.
    
    Parameters
    ----------
    year : int
        Year of the OGLE alerts you want.
        Valid choices are 2001 - 2019, inclusive.
        
    Outputs
    -------
    sqlite table called ogle_alerts_<YYYY> in microlensing.db
    Columns are alert_name, tE, Ibase, alert_url.
    """
    # Go to the OGLE alerts site and scrape the page.
    year = str(year)
    url = "https://ogle.astrouw.edu.pl/ogle4/ews/" + year + "/ews.html"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")

    # Figure out how many alert pages there are.
    npages = len(soup.find_all('td')[0::15])
    
    _t0 = time.time()     
    num_workers = mp.cpu_count()  
    pool = mp.Pool(processes=num_workers)
    parallel_results = pool.starmap(get_ogle_params, zip(repeat(year), range(npages)))
    _t1 = time.time() 

    # Put it all into a dataframe and write out to the database.
    df = pd.DataFrame(parallel_results,
                     columns =['RA', 'Dec', 'Tmax', 'Tmax_e', 'tau', 'tau_e', 
                               'Umin', 'Umin_e', 'Amax', 'Amax_e', 'Dmag', 'Dmag_e', 
                               'fbl', 'fbl_e', 'Ibl', 'Ibl_e', 'I0', 'I0_e'])

    df.to_sql(con=engine, schema=None, name="ogle_alerts_" + year, if_exists="replace", index=False)
    
    print('Took {0:.2f} seconds'.format(_t1-_t0))
    
def get_kmtnet_alerts(year):
    """
    Function that grabs KMTNet alerts and writes the fit
    tE and Ibase parameters, as well as each alert's 
    classification, to a table in the database.
    
    Parameters
    ----------
    year : int
        Year of the KMTNet alerts you want.
        Valid choices are 2016 - 2022, inclusive.
        
    Outputs
    -------
    sqlite table called kmtnet_alerts_<YYYY> in microlensing.db
    Columns are alert_name, class, tE, Ibase, alert_url.
    """
    def kmtnet_str_to_float(item):
        try:
            return float(ne.evaluate(item.get_text().replace(u'\xa0', u'')))
        except:
            return
        
    # Go to the KMTNet alerts site and scrape the page.
    year = str(year)
    url = "https://kmtnet.kasi.re.kr/~ulens/event/" + year + "/"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")

    # For some annoying reason, the KMTNet alerts system changes
    # across years randomly. Some years they report a single
    # classification for alerts, other years there are two 
    # classifications ("EF" and "AL", I don't know what it means).
    # For years where there are two classifications, I've picked 
    # AL classification arbitrarily.
    if year in ['2022', '2020', '2017', '2016']:
        tE = soup.find_all('td')[7::15][1:]
        Ibase = soup.find_all('td')[10::15][1:]
        cat = soup.find_all('td')[3::15][1:]
    elif year in ['2021', '2019', '2018']:
        tE = soup.find_all('td')[8::16][1:]
        Ibase = soup.find_all('td')[11::16][1:]
        cat = soup.find_all('td')[4::16][1:]
    else:
        raise Exception('Not a valid year')

    # Process output to get strings/floats as appropriate.
    tE_list = [kmtnet_str_to_float(item) for item in tE]
    Ibase_list = [kmtnet_str_to_float(item) for item in Ibase]
    cat_list = [item.get_text().replace(u'\xa0', u'') for item in cat]

    # Get link to the alert page.
    if year in ['2022', '2020', '2017', '2016']:
        alert_url = soup.find_all('td')[0::15][1:]
    elif year in ['2021', '2019', '2018']:
        alert_url = soup.find_all('td')[0::16][1:]
    else:
        raise Exception('Not a valid year')
    kmt_alert_url = 'https://kmtnet.kasi.re.kr/~ulens/event/' + year + '/'
    alert_url_list = [kmt_alert_url + item.find_all('a', href=True)[0]['href'] for item in alert_url]

    # Get alert name
    nn = len(tE_list)
    alert_name = []
    for ii in np.arange(nn):
        alert_name.append('KB' + year[2:] + str(ii+1).zfill(4))

    # Put it all into a dataframe and write out to the database.
    df = pd.DataFrame(list(zip(alert_name, cat_list, tE_list, Ibase_list, alert_url_list)),
                     columns =['alert_name', 'class', 'tE', 'Ibase', 'alert_url'])

    df.to_sql(con=engine, schema=None, name="kmtnet_alerts_" + year, if_exists="replace", index=False)
