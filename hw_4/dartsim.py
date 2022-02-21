
from random import uniform
import numpy as np 
from time import time

from dask.distributed import Client
client = Client(n_workers=8)
from dask import delayed

from multiprocessing import Pool
import dask.array as da

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
        ncircle = throw_and_sum(ndarts)
        approx = ncircle*4 / ndarts
        return approx
    
    elif parallel == 'pool':
        pool = Pool(processes=8)
        ncircle = pool.map(throw, range(ndarts))
        pool.terminate()
        del pool
        approx = np.sum(ncircle)*4 / ndarts
        return approx
    
    elif parallel == 'dask':
        if ndarts <= 10**5:
            chunks=ndarts
        else:
            chunks=10**5
        x = da.random.random(ndarts, chunks=chunks)
        y = da.random.random(ndarts, chunks=chunks)
        z = da.where((x - 0.5)**2 + (y - 0.5)**2 <= 0.25)[0]
        result = len(z.compute())
        approx = result*4 / ndarts
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
