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

```sh
python main.py [args]
```

```text
--method Heuristic|BeamSearch|EvoTADASHI(default)
--benchmark all|polybench nem (e.g. gemm)|jacobi-1d(default)
--dataset MINI|SMALL|LARGE(default)|EXTRALARGE
```

for other arguments, check the main.py file

## Polybench EvoTADASHI examples

`examples/polybench_evotadashi.py` runs EvoTADASHI on a concrete Polybench app.
Use `--cls Pet` or `--cls Polly` to choose the translator. Polybench benchmarks
can be specified by filename only; for example, use `cholesky` instead of
`linear-algebra/solvers/cholesky`.

Minimal example:

```sh
python -u examples/polybench_evotadashi.py \
  --cls Pet \
  --benchmark cholesky \
  --dataset EXTRALARGE \
  --population-size 300
```

For Polly, load the desired LLVM environment first:

```sh
module load LLVM/llvmorg-21.1.0
python -u examples/polybench_evotadashi.py --cls Polly --benchmark cholesky
```

Use `python -u examples/polybench_evotadashi.py --help` for the complete list of
parameters.

## Fugaku PJSub generation

`scripts/generate_polybench_evotadashi_pjsub.py` generates PJSub scripts for a
Polybench EvoTADASHI experiment matrix.

```sh
python scripts/generate_polybench_evotadashi_pjsub.py cholesky gemm
```

It writes job scripts under `jobs/polybench_evotadashi/` and a submit-all script:

```sh
jobs/polybench_evotadashi/run_all.sh
```

Run the generator without benchmark arguments to include all Polybench benchmarks.
Use `python scripts/generate_polybench_evotadashi_pjsub.py --help` for the
complete list of parameters.

Submit the generated jobs with:

```sh
jobs/polybench_evotadashi/run_all.sh
```

---

### References:

[1] TADASHI: https://arxiv.org/abs/2410.03210

[2] EvoTADASHI: (to be published at EvoAPPs'26 in April 2026)

```bibtex
@InProceedings{evotadashi,
  author = "Batista, Jo{\~a}o Eduardo
            and Vatai, Emil
            and Drozd, Aleksandr
            and Wahib, Mohamed",
  editor = "Garc\’ia-S\’anchez, Pablo
            and D\’iaz-\’Alvarez, Josefa,
            and Murphy, Aidan",
  title = {{EvoTADASHI: Genetic Programming for High-Performance Code Optimization}},
  booktitle = "Applications of Evolutionary Computation",
  year = 2026,
  publisher = "Springer Nature Switzerland",
  address = "Cham",
}
```

[3] Beam Search on TADASHI: please cite [2]

[4] Heuristic on TADASHI: please cite [1] or [2]
