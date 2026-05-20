#!/bin/env python

import argparse
import os
import shlex
from pathlib import Path

from tadashi.apps import Polybench

CONFIGS = [
    {
        "name": "pet",
        "cls": "Pet",
        "env": [],
    },
    {
        "name": "polly-llvm19",
        "cls": "Polly",
        "env": ["source /home/apps/oss/llvm-v19.1.4/init.sh"],
    },
    {
        "name": "polly-llvm21",
        "cls": "Polly",
        "env": ["module load LLVM/llvmorg-21.1.0"],
    },
]


JOB_TEMPLATE = r"""#!/bin/bash
#PJM -g {pjm_group}
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -N {job_name}
#PJM -L rscgrp={resource_group}
#PJM -L elapse={elapse}
#PJM -L node={nodes}
#PJM --mpi "max-proc-per-node=1"
# #PJM --llio localtmp-size=40Gi
#PJM -j -S

set -e

export TMPDIR=/worktmp
export LD_PRELOAD=/usr/lib/FJSVtcs/ple/lib64/libpmix.so

{env}

PYTHON_BIN={python_bin}
ENTRYPOINT=examples/polybench_evotadashi.py
RESULT_DIR={result_dir}
RESULT_FILE=$RESULT_DIR/run{run_index}.txt

{mpi_args}

{app_args}

{ml_args}

mkdir -p "$RESULT_DIR"
{{
  "${{MPI_ARGS[@]}}" "$PYTHON_BIN" -u "$ENTRYPOINT" \
    "${{APP_ARGS[@]}}" \
    "${{ML_ARGS[@]}}"
}} > "$RESULT_FILE" 2>&1
"""


BASH_ARRAY_TEMPLATE = r"""{name}=(
{values}
)"""


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir", type=Path, default=Path("jobs/polybench_evotadashi")
    )
    parser.add_argument(
        "--results-dir", type=Path, default=Path("results/polybench_evotadashi")
    )
    parser.add_argument("--dataset", type=str, default="EXTRALARGE")
    parser.add_argument("--oflag", type=int, default=3)
    parser.add_argument("--population-size", type=int, default=300)
    parser.add_argument("--max-gen", type=int, default=20)
    parser.add_argument("--n-trials", type=int, default=2)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--elapse", type=str, default="21:00:00")
    parser.add_argument("--resource-group", type=str, default="small")
    parser.add_argument("--pjm-group", type=str, default="ra000012")
    parser.add_argument("--python", type=str, default="python")
    parser.add_argument("--mpirun", type=str, default="mpirun")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("benchmarks", nargs="*")
    return parser


def benchmark_name(benchmark):
    return Path(str(benchmark)).name


def get_benchmarks(selected):
    if selected:
        return [benchmark_name(benchmark) for benchmark in selected]
    return [benchmark_name(benchmark) for benchmark in Polybench.get_benchmarks()]


def bash_array(name, values):
    return BASH_ARRAY_TEMPLATE.format(
        name=name,
        values="\n".join(
            "  {value}".format(value=shlex.quote(value)) for value in values
        ),
    )


def build_job(args, config, benchmark, run_index):
    seed = args.seed + run_index
    result_dir = args.results_dir / args.dataset / config["name"] / benchmark
    job_name = "EvoT_{config}_{benchmark}_r{run_index}".format(
        config=config["name"],
        benchmark=benchmark,
        run_index=run_index,
    )

    return JOB_TEMPLATE.format(
        pjm_group=args.pjm_group,
        job_name=job_name[:63],
        resource_group=args.resource_group,
        elapse=args.elapse,
        nodes=args.population_size + 1,
        env="\n".join(config["env"]),
        python_bin=shlex.quote(args.python),
        result_dir=shlex.quote(str(result_dir)),
        run_index=run_index,
        mpi_args=bash_array("MPI_ARGS", [args.mpirun, "-n", "1"]),
        app_args=bash_array(
            "APP_ARGS",
            [
                "--cls={cls}".format(cls=config["cls"]),
                "--benchmark={benchmark}".format(benchmark=benchmark),
                "--dataset={dataset}".format(dataset=args.dataset),
                "--oflag={oflag}".format(oflag=args.oflag),
            ],
        ),
        ml_args=bash_array(
            "ML_ARGS",
            [
                "--population-size={population_size}".format(
                    population_size=args.population_size
                ),
                "--max-gen={max_gen}".format(max_gen=args.max_gen),
                "--n-trials={n_trials}".format(n_trials=args.n_trials),
                "--init_seed={seed}".format(seed=seed),
                "--use-mpi",
            ],
        ),
    )


def main():
    args = get_parser().parse_args()
    benchmarks = get_benchmarks(args.benchmarks)
    run_all = []

    for config in CONFIGS:
        for benchmark in benchmarks:
            for run_index in range(args.runs):
                filename = "{benchmark}_run{run_index}.sh".format(
                    benchmark=benchmark,
                    run_index=run_index,
                )
                path = args.output_dir / config["name"] / filename
                run_all.append("pjsub {path}".format(path=path))

                if args.dry_run:
                    continue

                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(build_job(args, config, benchmark, run_index))

    run_all_path = args.output_dir / "run_all.sh"
    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        run_all_path.write_text("\n".join(run_all) + "\n")
        os.chmod(run_all_path, 0o755)

    print("configs:", ", ".join(config["name"] for config in CONFIGS))
    print("benchmarks:", len(benchmarks))
    print("runs per config/benchmark:", args.runs)
    print("jobs:", len(run_all))
    print("run all:", run_all_path)


if __name__ == "__main__":
    main()
