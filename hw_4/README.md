Casey Lam (casey_lam@berkeley.edu)

Homework 4 for Ay250, Spring 2022.

Submission: Sunday February 20, 2022.

The top plot shows the difference in runtime of different parallelization methods
as a function of the number of dart throws simulated (solid line) with the standard
deviation of 10 trials shown as the shading. The number of darts simulated per second
is shown as the dashed line. For simple (i.e. no) parallelization, simulation time
rises linearly with number of darts thrown, and the number of darts simulated per
second is roughly constant. On the other hand, using Pool or dask to parallelize
the dart throws resuls in a roughly constant runtime up to a certain point, after which
the runtime increases. Correspondingly, the number of darts simulated per second is
increasing but beings to taper when the runtime begins to increase. For small
(less than 10^4 - 10^5) dart throws, the overhead from parallelization causes the
runtime to be longer than the simple unparallelized case. However, beyond that,
parallelization helps speed up the runtime.

The bottom plot is just for fun, to see how the error on the approximation of pi
scales with the number of darts thrown. And also to make sure that the results
agree within the uncertainties, no matter what parallelization scheme is used!