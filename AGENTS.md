# Repository Guidelines

## Project Structure & Module Organization

`ml4tadashi/` contains the Python package. Core algorithms live in separate modules such as `EvoTADASHI.py`, `BeamSearch.py`, `Heuristic.py`, and `ReinforcementLearning.py`. The package is responsible for ML algorithms that operate on `tadashi.App` instances; it should not construct, import, or depend on concrete benchmark apps such as `Polybench`. `examples/` holds runnable usage examples for MPI, transformations, and concrete app setup. `scripts/` contains helper scripts for result comparison and batch submission generation, including Fugaku/PJSub utilities. Packaging metadata is in `pyproject.toml`; GitHub Actions configuration is under `.github/workflows/`.

## Responsibility Boundaries

`tadashi` provides the `tadashi.App` base class and owns concrete app implementations. `Polybench` is one concrete app provided by `tadashi`.

`ml4tadashi` owns ML optimization algorithms that consume an app object of type `tadashi.App` or an app factory returning compatible instances. Package code should stay generic over that interface and avoid Polybench-specific options, paths, translators, benchmark datasets, or compiler flags.

Polybench and other concrete app setup belongs in `examples/` or other example-only scripts. Example scripts may import `tadashi.apps.Polybench`, choose translators, and configure benchmark-specific compiler options before passing the resulting app into `ml4tadashi` algorithms.

## Build, Test, and Development Commands

Install locally in editable mode:

```bash
python -m pip install -e .
```

Build source and wheel distributions, matching the publish workflow:

```bash
python -m pip install build
python -m build --sdist --wheel --outdir dist .
```

Run an example:

```bash
python examples/example_transformation.py
python examples/example_mpi4py.py
```

Examples require the external TADASHI runtime and related compiler/MPI tools to be installed.

## Coding Style & Naming Conventions

Use Python 3.7-compatible syntax, as declared in `pyproject.toml`. Follow the existing style: 4-space indentation, short procedural scripts, and algorithm classes named in PascalCase (`EvoTADASHI`, `BeamSearch`, `Heuristic`). Prefer snake_case for functions, variables, and command-line arguments. Keep new algorithm implementations in `ml4tadashi/`, keep concrete `tadashi.App` wiring in `examples/`, and reserve `scripts/` for operational helpers.

## Testing Guidelines

There is no dedicated test suite in the current tree. When adding tests, place them under `tests/` and name files `test_*.py` so `pytest` can discover them. For changes that touch optimization behavior, add small deterministic tests around argument handling or transformation-list construction, and document any TADASHI/compiler prerequisites. Until tests exist, validate changes by running the relevant example script.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries such as `Create pyproject.toml` and `Update to setup-python@v6`. Keep commit messages concise and focused on one change. Pull requests should include a brief description, commands run, environment notes for TADASHI/MPI/compiler dependencies, and any relevant benchmark or output differences. Link related issues when available and avoid committing generated artifacts such as `dist/`, caches, or local benchmark outputs.

## Security & Configuration Tips

Do not commit credentials, cluster account details, or local machine paths. Keep PyPI publishing secrets in GitHub repository secrets; the workflow only publishes on tag refs.
