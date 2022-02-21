
from random import uniform
import numpy as np 
from time import time, sleep
import matplotlib.pyplot as plt

from dask.distributed import Client
client = Client(n_workers=8)
from dask import delayed

from multiprocessing import Pool
import dask.array as da

import matplotlib
font = {'size'   : 22}
lines = {'linewidth' : 2}

matplotlib.rc('font', **font)
matplotlib.rc('lines', **lines)

def simulate(ndarts, parallel):
    """
    Input
    -----
    ndarts : int
        Number of darts to simulate throwing.
        
    parallel : str
        Parallelization. 'simple', 'pool', or 'dask'.
          
    Return
    ------
    approx : float
        Approximation to pi.
    """
    if parallel == 'simple':
        ncircle = throw_and_sum(dart)
        approx = ncircle*4 / dart
        return approx
    
    elif parallel == 'pool':
        pool = Pool(processes=8)
        ncircle = pool.map(throw, range(dart))
        pool.terminate()
        del pool
        approx = np.sum(ncircle)*4 / dart
        return approx
    
    elif parallel == 'dask':
        if ndarts <= 10**5:
            chunks=ndarts
        else:
            chunks=10**5
        x = da.random.random(dart, chunks=chunks)
        y = da.random.random(dart, chunks=chunks)
        z = da.where((x - 0.5)**2 + (y - 0.5)**2 <= 0.25)[0]
        result = len(z.compute())
        approx = result*4 / dart
        return approx
    
    else:
        raise Exception('That\'s not a valid choice for parallel.')
        
def throw(dummy_var):
    """
    Simulate throwing a dart at a circle inscribed by a square.
    Returns 1 if dart falls within circle, 0 otherwise.
    
    Input
    -----
    dummy_var : int
        Dummy variable for iteration purposes. 
        
    Return 
    ------
    ndart : Either 0 or 1.
    """
    x, y = uniform(0, 1), uniform(0, 1)
    if np.hypot(x-0.5, y-0.5) <= 0.5:
        return 1
    else:
        return 0

def throw_and_sum(number_of_darts):
    """
    Simulate throwing darts at a circle inscribed by a square.
    Returns total number of darts that land in circle.
    
    Input
    -----
    number_of_darts : int
        Number of darts to throw.
        
    Return 
    ------
    number_of_darts_in_circle : int
        Number of darts that landed in the circle.
    """
    # Variable to store number of darts that land in circle
    number_of_darts_in_circle = 0

    # Figure out what darts land in the circle.
    for n in range(number_of_darts):
        x, y = uniform(0, 1), uniform(0, 1)
        if np.hypot(x-0.5, y-0.5) <= 0.5:
            number_of_darts_in_circle += 1

    return number_of_darts_in_circle

# Let's try throwing different numbers of darts to see how the time scales.
ndarts = np.array([10, 10**2, 10**3, 10**4, 10**5, 10**6, 10**7])

ntrials = 10

t_simple = np.empty((len(ndarts), ntrials))
t_pool =  np.empty((len(ndarts), ntrials))
t_dask = np.empty((len(ndarts), ntrials))
pi_simple = np.empty((len(ndarts), ntrials))
pi_pool =  np.empty((len(ndarts), ntrials))
pi_dask = np.empty((len(ndarts), ntrials))

parallel = ['simple', 'pool', 'dask']
times = [t_simple, t_pool, t_dask]
pi_approx = [pi_simple, pi_pool, pi_dask]

for kk, par in enumerate(parallel):
    for jj in range(ntrials):
        for ii, dart in enumerate(ndarts):
            start_time = time()
            pi_approx[kk][ii, jj] = simulate(dart, par)
            end_time = time()
            times[kk][ii, jj] = end_time - start_time
            
fig, ax = plt.subplots(figsize=(15, 12))
ax.plot(ndarts, t_simple.mean(axis=1), label='Simple', color='red')
ax.fill_between(ndarts, t_simple.mean(axis=1) - t_simple.std(axis=1), 
                t_simple.mean(axis=1) + t_simple.std(axis=1),
                color='red', alpha=0.3)

ax.plot(ndarts, t_pool.mean(axis=1), label='Pool', color='cyan')
ax.fill_between(ndarts, t_pool.mean(axis=1) - t_pool.std(axis=1), 
                t_pool.mean(axis=1) + t_pool.std(axis=1),
                color='cyan', alpha=0.3)

ax.plot(ndarts, t_dask.mean(axis=1), label='Dask', color='black')
ax.fill_between(ndarts, t_dask.mean(axis=1) - t_dask.std(axis=1), 
                t_dask.mean(axis=1) + t_dask.std(axis=1),
                color='black', alpha=0.3)

ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Darts thrown')
ax.set_ylabel('Execution Time (sec), solid line')

ax_r = ax.twinx()
ax_r.plot(ndarts, ndarts/t_simple.mean(axis=1), '--',label='Simple', color='red')
ax_r.plot(ndarts, ndarts/t_pool.mean(axis=1), '--', label='Pool', color='cyan')
ax_r.plot(ndarts, ndarts/t_dask.mean(axis=1), '--', label='Dask', color='black')
ax_r.set_ylabel('Simulation Rate (darts/sec), dashed line')
ax_r.set_yscale('log')
ax.legend()
plt.show()
