# Machine Learning for TADASHI

This repository contains several machine learning methods applied to TADASHI [1]

## TADASHI

...

## Machine Learning Algorithms

Using the ML4TADASHI repository, solutions are viewed as a list of transformations (and respective parameters) to be applied to the original code.

In this sense, an empty transformation list represents the original code, i.e., code without transformations.

Solutions such as the example below represent a list that applies the TILE2D transformation to SCoP 0, band 1, with a tile size of 32 in both for loops:

solution = [ [0, 1, TILE2D, 32, 32], ]

Since transformations can be stacked, the objective of this repository is to find a good list of transformations to be applied to the code in the hardware system on which it is being run.


### EvoTADASHI

EvoTADASHI [2] is an algorithm based on genetic programming, applied to TADASHI.

Using EvoTADASHI, there are 2 ways to bootstrap evolution: either the initial population is a single solution consisting of an empty transformation list, or we bootstrap it using the heuristic algorithm described below. Starting from an empty transformation list guarantees that, in the worst case, the solution found is the original code.

Currently, there is no crossover method implemented. The mutation operator looks at the current transformation list, obtains a list of possible next transformations, and picks one at random. The arguments for this transformation are selected using the random_args() function.

...

### Beam Search

Beam Search on TADASHI [3] is...

...

### Heuristic

The heuristic approach [1,2], while not being a machine learning method, is used by EvoTADASHI in its paper.
This heuristic proposed a list of transformations using a single evaluation, making it a computationally cheap approach to use by itself or to bootstrap other algorithms.

Using this approach, we simply apply TILE3D, TILE2D, and FULL_SPLIT whenever possible. In preliminary results, this led to some performance improvements, making it a cheap way to add possibly good solutions to the list of solutions.

...


## How to use:

$ python main.py [args]

--method Heuristic|BeamSearch|EvoTADASHI(default)

--benchmark all|polybench nem (e.g. gemm)|jacobi-1d(default)

--dataset MINI|SMALL|LARGE(default)|EXTRALARGE

for other arguments, check the main.py file

---

### References:

[1] TADASHI: https://arxiv.org/abs/2410.03210

[2] EvoTADASHI: 

@inproceedings{BatistaJE26,
author = {Batista, Jo\~{a}o Eduardo and Vatai, Emil and Drozd, Aleksandr and Wahib, Mohamed},
title = {{EvoTADASHI}: Genetic Programming for High-Performance Code Optimization},
year = {2026},
isbn = {978-3-032-23603-6},
publisher = {Springer-Verlag},
address = {Berlin, Heidelberg},
url = {https://doi.org/10.1007/978-3-032-23604-3_3},
doi = {10.1007/978-3-032-23604-3_3},
booktitle = {Applications of Evolutionary Computation: 29th European Conference, EvoApplications 2026, Held as Part of EvoStar 2026, Toulouse, France, April 8–10, 2026, Proceedings, Part I},
pages = {35–51},
numpages = {17},
keywords = {Evolutionary Computation, Genetic Programming, High Performance Computing, Polyhedral Model, Code Transformation, Code Correctness},
location = {Toulouse, France}
}

[3] Beam Search on TADASHI: please cite [2]

[4] Heuristic on TADASHI: please cite [1] or [2]

