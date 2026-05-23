#!/bin/env python

import argparse
import os
from datetime import datetime
from pathlib import Path
from shlex import quote

from tadashi.apps import Polybench

REPO_ROOT = Path(__file__).resolve().parents[1]

CONFIGS = [
    {
        "name": "pet",
        "translator": "Pet",
        "env": [],
    },
    {
        "name": "polly-llvm19",
        "translator": "Polly",
        "env": ["source /home/apps/oss/llvm-v19.1.4/init.sh"],
    },
    {
        "name": "polly-llvm21",
        "translator": "Polly",
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
#PJM -S

set -e

export TMPDIR=/worktmp
export LD_PRELOAD=/usr/lib/FJSVtcs/ple/lib64/libpmix.so

{env}

ENTRYPOINT={entrypoint}
RESULT_DIR={result_root}/job_$PJM_JOBID

MPIRUN=(
  mpirun -n 1
  -stdout-proc "$RESULT_DIR/run{run_index}.out"
  -stderr-proc "$RESULT_DIR/run{run_index}.err"
)

FLAGS=(
{flags}
)

mkdir -p "$RESULT_DIR"
"${{MPIRUN[@]}}" python -u "${{ENTRYPOINT}}" "${{FLAGS[@]}}"
"""


def get_parser():
    parser = argparse.ArgumentParser(
        description="Generate Fugaku PJSub scripts for Polybench EvoTADASHI runs."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("jobs/polybench_evotadashi"),
        help="Directory where generated PJSub scripts are written.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results/polybench_evotadashi"),
        help="Base directory used by generated jobs for run output.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="EXTRALARGE",
        help="Polybench dataset size passed to the runner.",
    )
    parser.add_argument(
        "--population-size",
        type=int,
        default=300,
        help="EvoTADASHI population size.",
    )
    parser.add_argument(
        "--max-gen",
        type=int,
        default=20,
        help="Maximum number of EvoTADASHI generations.",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=2,
        help="Number of evaluation trials per individual.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Independent seeded runs generated for each config and benchmark.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Initial seed; run N uses seed + N.",
    )
    parser.add_argument(
        "--elapse",
        type=str,
        default="21:00:00",
        help="PJSub wall-time limit for each generated job.",
    )
    parser.add_argument(
        "--pjm-group",
        type=str,
        default="ra000012",
        help="PJSub project/group name.",
    )
    parser.add_argument(
        "--nodes",
        type=int,
        default=None,
        help="Allocated PJSub nodes. Defaults to population size + 1.",
    )
    parser.add_argument(
        "benchmarks",
        nargs="*",
        help="Optional Polybench benchmarks; filenames like cholesky are enough.",
    )
    return parser


def result_root(results_dir, dataset, timestamp, config, benchmark, run_index):
    subdir = f"{dataset}-{config['name']}-{benchmark}-run{run_index}"
    path = results_dir / subdir / timestamp
    return path.resolve()


def build_submission(path, result_root_path):
    pjsub_stdout = result_root_path / "pjsub.%j.out"
    pjsub_stderr = result_root_path / "pjsub.%j.err"
    return "\n".join(
        [
            f"mkdir -p {quote(str(result_root_path))}",
            "pjsub \\",
            f"  -o {quote(str(pjsub_stdout))} \\",
            f"  -e {quote(str(pjsub_stderr))} \\",
            f"  {quote(str(path.resolve()))}",
        ]
    )


def build_job(args, timestamp, config, benchmark, run_index):
    seed = args.seed + run_index
    result_root_path = result_root(
        args.results_dir, args.dataset, timestamp, config, benchmark, run_index
    )
    job_name = f"EvoT_{config['name']}_{benchmark}_r{run_index}"

    flags = [
        f"--translator={config['translator']}",
        f"--benchmark={benchmark}",
        f"--dataset={args.dataset}",
        f"--population-size={args.population_size}",
        f"--max-gen={args.max_gen}",
        f"--n-trials={args.n_trials}",
        f"--init_seed={seed}",
        "--use-mpi",
    ]
    return JOB_TEMPLATE.format(
        pjm_group=args.pjm_group,
        job_name=job_name,
        resource_group="small",
        elapse=args.elapse,
        nodes=args.nodes or args.population_size + 1,
        env="\n".join(config["env"]),
        entrypoint=quote(str(REPO_ROOT / "examples/polybench_evotadashi.py")),
        result_root=quote(str(result_root_path)),
        run_index=run_index,
        flags="\n".join(f"  {quote(f)}" for f in flags),
    )


def main():
    args = get_parser().parse_args()
    benchmarks = args.benchmarks if args.benchmarks else Polybench.get_benchmarks()
    benchmarks = [Path(str(benchmark)).name for benchmark in benchmarks]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_all = []

    for config in CONFIGS:
        for benchmark in benchmarks:
            for run_index in range(args.runs):
                filename = f"{benchmark}_run{run_index}.sh"
                path = args.output_dir / config["name"] / filename
                root = result_root(
                    args.results_dir,
                    args.dataset,
                    timestamp,
                    config,
                    benchmark,
                    run_index,
                )
                run_all.append(build_submission(path, root))
                path.parent.mkdir(parents=True, exist_ok=True)
                body = build_job(args, timestamp, config, benchmark, run_index)
                path.write_text(body)

    run_all_path = args.output_dir / "run_all.sh"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    submissions = "\n\n".join(run_all)
    run_all_path.write_text(f"#!/bin/bash\nset -e\n\n{submissions}\n")
    os.chmod(run_all_path, 0o755)

    print("configs:", ", ".join(config["name"] for config in CONFIGS))
    print("benchmarks:", len(benchmarks))
    print("runs per config/benchmark:", args.runs)
    print("jobs:", len(run_all))
    print("timestamp:", timestamp)
    print("run all:", run_all_path)


if __name__ == "__main__":
    main()
