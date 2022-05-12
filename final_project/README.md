# MAD 
Microlensing Alerts Database (MAD) is a Flask webapp that allows the user to 
interact with a database of event parameters and lightcurves from the
[MOA](http://www.massey.ac.nz/~iabond/moa/alerts/), 
[OGLE](https://ogle.astrouw.edu.pl/ogle4/ews/), and
[KMTNet](https://kmtnet.kasi.re.kr/~ulens/)
microlensing alert websites.

With MAD, the user can query the database and download the results as a CSV file.

In addition, the user can use the query to view lightcurves.

### Background and motivation:
Our research group is looking for isolated stellar mass black holes with microlensing.
We want to choose promising black hole candidates from photometric microlensing 
alert systems to follow up astrometrically for our HST Cycle 29 program.
The way we've done this in the past is to look through individual alert pages for events of interest.
However, this is not ideal for many reasons:
1. It is very time consuming to click through each alert page one at a time to look at lightcurves.
Although all the fit parameters are located on the home page, MOA and OGLE report uncertainties 
on their parameters which are only shown on the individual event pages.
2. The active alert page for the current year are updated on a regular (nightly) basis.
This means that the reported best-fit microlensing model parameters also get updated, 
so an event that looks promising might not be so good two weeks later or vice versa.  
3. Sometimes we want to re-analyze a set of lightcurves, 
and having to go page by page to download what we want is also time consuming.
4. Combining all the issues above leads to a general mess.
This also makes the process likely less thorough.
5. For MOA in particular, the lightcurves provided for visualization on the alert website
are shown as difference image lightcurves, i.e. delta flux vs. time. 
However, this is impossible to interpret in the sense that we care about (i.e. what is the
difference between the baseline and peak magnification?)

### Goal of MAD: 
MAD was created to help alleviate these issues.
By aggregating all the alerts into a database, we can easily query a table of 
alert parameters to find the events that are most promising.
Then, we can use JOIN queries to grab the photometry data for those events
to re-analyze and visualize ourselves.
The database can then also be easily updated to grab the latest changes, and
the same query can be re-run, to see what changes.

### General structure
There are three files:
1. *app.py*. 
This is the Flask app itself.
2. *query_alerts.py*. 
This is a module that contains a bunch of functions 
that can be used to  populate the database.
It primarily consists of functions that scrape microlensing event alerts 
and lightcurves from the OGLE, KMTNet, and MOA websites.
3. *populate_database.py*.
This is a very short script that calls query_alerts.py that populates the database.

Before the Flask app can be used, populate_database.py must be run.

### Final project practicalities
This project uses a lot of concepts from the web and databases lectures.
There is also a bit of numpy/pandas and parallelization usage.

### Future work (aka things I did not get to)
In no particular order...
1. Parallelize lightcurve download (currently ~1 hour for each alert system year). 
Need to figure out parallel writing to SQL database (is that allowed) as well as
how to parallelize ftp downloads.
2. Add a table of duplicated/crossmatched events across the three systems.
MOA and KMTNet already provide this information.
I just need to scrape it and put it into a new table.
3. Save less decimals for some of the numbers in the table (like HJD or mag).
4. Implementing some automated way of updating the database.
(See notes from meeting with Josh.)
5. More unit tests (of course).
