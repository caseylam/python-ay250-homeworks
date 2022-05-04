
# FIXME: ONLY DOWNLOAD ALERT YEAR + PREVIOUS YEAR (otherwise tooons of data.)

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
engine = create_engine('sqlite:///microlensing.db')
conn = engine.connect()

def get_moa_lightcurves(year):
    # So we don't have to deal with the log10 complaining.
    import warnings
    warnings.filterwarnings("ignore")

    year = str(year)

    url = "http://www.massey.ac.nz/~iabond/moa/alert" + year + "/alert.php"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")
    links = soup.find_all('a', href=True)
    alert_dirs = []
    # Get a list of all the bulge microlensing alerts
    for ii, link in enumerate(links):
        if 'BLG' in link.text:
            alert_dirs.append(links[ii]['href'])

    for nn, alert_dir in enumerate(alert_dirs[0:10]):
        url = "http://www.massey.ac.nz/~iabond/moa/alert" + year + "/" + alert_dir
        response = urlopen(url)
        html = response.read()
        response.close()
        soup = BeautifulSoup(html,"html.parser")

        # Get the magnitude and flux offsets.
        foo = soup.find('b').next_sibling
        moff = foo.split('=')[1].split('-')[0].strip(' ')
        bah = soup.find('sub').next_sibling
        foff = bah.split('+')[1].split(')')[0].strip(' ')

        # Now convert these into floats
        m = ne.evaluate(moff)
        f = ne.evaluate(foff)

        # Now scrape the .dat file into a pandas dataframe.
        url = "https://www.massey.ac.nz/~iabond/moa/alert" + year + "/fetchtxt.php?path=moa/ephot/phot-" + \
                alert_dir.strip('display.php?id=') + ".dat"
        bytes_data = requests.get(url).content
        df = pd.read_csv(BytesIO(bytes_data), 
                         delim_whitespace=True, skiprows=11, skipfooter=1, header=None, engine='python', 
                         names=['hjd', 'delta_flux', 'flux_err', 'foo1', 'foo2', 'foo3', 'foo4', 'foo5'])

        df['mag'] = m - 2.5*np.log10(df['delta_flux'] + f)
        df['mag_err'] = 1.09 * df['flux_err']/(df['delta_flux'] + f)
        df['alert_name'] = 'MB' + year[2:] + str(nn + 1).zfill(3)  # need to make sure this always works.
        
        df['hjd'] -= 2450000

        df.dropna(axis='index', how='any', inplace=True)

        cols = ['hjd', 'mag', 'mag_err', 'alert_name']
        df[cols].to_sql(con=engine, schema=None, name="moa_" + year, if_exists="append", index=False)
        
def get_ogle_lightcurves(year):
    year = str(year)

    ftp = ftplib.FTP("ftp.astrouw.edu.pl")
    ftp.login()
    ftp.cwd("ogle/ogle4/ews/" + year + "/")

    for nn in np.arange(start=1, stop=10, step=1):
        ftp.cwd("blg-" + str(nn).zfill(4))

        flo = BytesIO()
        ftp.retrbinary('RETR phot.dat', flo.write)
        flo.seek(0)
        df = pd.read_fwf(flo, header=0, names=['hjd', 'mag', 'mag_err', 'see', 'sky'])

        df['alert_name'] = 'OB' + year[2:] + str(nn + 1).zfill(4) 

        cols = ['hjd', 'mag', 'mag_err', 'alert_name']
        df[cols].to_sql(con=engine, schema=None, name="ogle_" + year, if_exists="append", index=False)

        ftp.cwd("../")
        
def get_kmtnet_lightcurves(year):
    year = str(year)
    
    for nn in np.arange(start=1, stop=11, step=1):
        # For KMTNet, get data from all the telescopes?
        url = "https://kmtnet.kasi.re.kr/~ulens/event/" + year + "/view.php?event=KMT-" + year + \
                "-BLG-" + str(nn).zfill(4)
        response = urlopen(url)
        html = response.read()
        response.close()
        soup = BeautifulSoup(html,"html.parser")

        links = soup.find_all('a', href=True)

        # Only keep I-band lightcurves. 
        pysis_names = links[3].get_text(separator=',').split(',')[:-2]
        for pysis_name in pysis_names:
            if '_I.pysis' in pysis_name:
                url = "https://kmtnet.kasi.re.kr/~ulens/event/" + year + "/data/KB" + \
                        year[2:] + str(nn).zfill(4) + "/pysis/" + pysis_name
                print(url)
                bytes_data = requests.get(url).content
                try:
                    df = pd.read_csv(BytesIO(bytes_data), 
                                     delim_whitespace=True, skiprows=1, header=None, 
                                     names=['hjd', 'Delta_flux', 'flux_err', 'mag', 'mag_err', 'fwhm', 'sky', 'secz'])

                    df['alert_name'] = 'KB' + year[2:] + str(nn).zfill(4) 
                    df['lightcurve'] = pysis_name

                    cols = ['hjd', 'mag', 'mag_err', 'lightcurve', 'alert_name']
                    df[cols].to_sql(con=engine, schema=None, name="kmtnet_" + year, if_exists="append", index=False)
                except:
                    print('This doesn\'t exist, skipping.'.format(nn))
                    continue
                    
def get_moa_alerts(year):
    year = str(year)

    url = "http://www.massey.ac.nz/~iabond/moa/alert2022/alert.php"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")

    
    # Grab columns for tE and Ibase.
    tE = soup.find_all('td')[4::8]
    Ibase = soup.find_all('td')[6::8]

    # Convert them from strings to floats.
    tE_list = [float(ne.evaluate(item.get_text())) for item in tE]
    Ibase_list = [float(ne.evaluate(item.get_text())) for item in Ibase]

    # Now, grab the classification column.
    cat = soup.find_all('td')[7::8]
    cat_list = [item.get_text() for item in cat]

    # Link to the alert page.
    alert_url = soup.find_all('td')[0::8]
    moa_alert_url = 'http://www.massey.ac.nz/~iabond/moa/alert' + year + '/'
    alert_url_list = [moa_alert_url + item.find_all('a', href=True)[0]['href'] for item in alert_url]

    # Alert name
    nn = len(tE_list)
    alert_name = []
    for ii in np.arange(nn):
        alert_name.append('MB' + year[2:] + str(ii+1).zfill(3))

    # Put it all into a dataframe.
    df = pd.DataFrame(list(zip(alert_name, cat_list, tE_list, Ibase_list, alert_url_list)),
                     columns =['alert_name', 'class', 'tE', 'Ibase', 'alert_url'])

    df.to_sql(con=engine, schema=None, name="moa_alerts_" + year, if_exists="replace", index=False)
    
def get_ogle_alerts(year):
    def ogle_str_to_float(item):
        try:
            return float(ne.evaluate(item.contents[0].replace(u'\n', '')))
        except:
            return

    year = str(year)
  
    # Get alerts using beautiful soup.
    url = "https://ogle.astrouw.edu.pl/ogle4/ews/" + year + "/ews.html"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")

    # Grab columns for tE and Ibase.
    tE = soup.find_all('td')[8::15] 
    Ibase = soup.find_all('td')[13::15]

    # Convert them from strings to floats.
    tE_list = [ogle_str_to_float(item) for item in tE]
    Ibase_list = [ogle_str_to_float(item) for item in Ibase]

    # Alert name and page link.
    nn = len(tE_list)
    alert_name = []
    alert_url_list = []
    ogle_alert_url = 'https://ogle.astrouw.edu.pl/ogle4/ews/'

    for ii in np.arange(nn):
        alert_name.append('OB' + year[2:] + str(ii+1).zfill(4))
        alert_url_list.append(ogle_alert_url + str(ii+1).zfill(4) + '.html')

    # Put it all into a dataframe.
    df = pd.DataFrame(list(zip(alert_name, tE_list, Ibase_list, alert_url_list)),
                     columns =['alert_name', 'tE', 'Ibase', 'alert_url'])

    df.to_sql(con=engine, schema=None, name="ogle_alerts_" + year, if_exists="replace", index=False)
    
def get_kmtnet_alerts(year):
    """
    year is an integer.
    """
    def kmtnet_str_to_float(item):
        try:
            return float(ne.evaluate(item.get_text().replace(u'\xa0', u'')))
        except:
            return

    year = str(year)
    url = "https://kmtnet.kasi.re.kr/~ulens/event/" + year + "/"
    response = urlopen(url)
    html = response.read()
    response.close()
    soup = BeautifulSoup(html,"html.parser")

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

    tE_list = [kmtnet_str_to_float(item) for item in tE]
    Ibase_list = [kmtnet_str_to_float(item) for item in Ibase]
    cat_list = [item.get_text().replace(u'\xa0', u'') for item in cat]

    # Link to the alert page.
    if year in ['2022', '2020', '2017', '2016']:
        alert_url = soup.find_all('td')[0::15][1:]
    elif year in ['2021', '2019', '2018']:
        alert_url = soup.find_all('td')[0::16][1:]
    else:
        raise Exception('Not a valid year')
    kmt_alert_url = 'https://kmtnet.kasi.re.kr/~ulens/event/' + year + '/'
    alert_url_list = [kmt_alert_url + item.find_all('a', href=True)[0]['href'] for item in alert_url]

    # Alert name
    nn = len(tE_list)
    alert_name = []
    for ii in np.arange(nn):
        alert_name.append('KB' + year[2:] + str(ii+1).zfill(4))

    # Put it all into a dataframe.
    df = pd.DataFrame(list(zip(alert_name, cat_list, tE_list, Ibase_list, alert_url_list)),
                     columns =['alert_name', 'class', 'tE', 'Ibase', 'alert_url'])

    df.to_sql(con=engine, schema=None, name="kmtnet_alerts_" + year, if_exists="replace", index=False)
