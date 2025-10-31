# Machine Learning for TADASHI

This repository contains several machine learning methods applied to TADASHI [1]

## TADASHI

...

## Machine Learning Algorithms

### EvoTADASHI

EvoTADASHI [2] is an algorithm based on genetic programming, applied to TADASHI.

...

### Beam Search

Beam Search on TADASHI [3] is...

...

### Heuristic

The heuristic approach [1,2], while not being a machine learning method, is used by EvoTADASHI in its paper.
This heuristic proposed a list of transformations using a single evaluation, making it a computationally cheap approach to use by itself or to bootstrap other algorithms.

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

[2] EvoTADASHI: (work in progress)

[3] Beam Search on TADASHI: please cite [2]

[4] Heuristic on TADASHI: please cite [1] or [2]

