#!/bin/env python

import argparse
import os
from datetime import datetime
from pathlib import Path
from shlex import quote

from tadashi.apps import Polybench

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


SUBMISSION_TEMPLATE = r"""#!/bin/bash
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_DIR=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)
RESULT_ROOT={result_root}
ENTRYPOINT="$REPO_DIR/examples/polybench_evotadashi.py"

mkdir -p "$RESULT_ROOT"

pjsub \
  -o "$RESULT_ROOT/pjsub.%j.stdout" \
  -e "$RESULT_ROOT/pjsub.%j.stderr" \
  --spath "$RESULT_ROOT/pjsub.%j.stat" \
  -x RESULT_ROOT="$RESULT_ROOT" \
  -x ENTRYPOINT="$ENTRYPOINT" <<'PJSUB_EOF'
#!/bin/bash
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

MPIRUN=(
  mpirun -n 1
  -stdout-proc "$RESULT_ROOT/pjsub.$PJM_JOBID.out"
  -stderr-proc "$RESULT_ROOT/pjsub.$PJM_JOBID.err"
)

FLAGS=(
{flags}
)

mkdir -p "$RESULT_ROOT"
"${{MPIRUN[@]}}" python -u "${{ENTRYPOINT}}" "${{FLAGS[@]}}"
PJSUB_EOF
"""

RUN_ALL_TEMPLATE = """#!/bin/bash
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

{submission}
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
        "--seed",
        type=int,
        default=42,
        help="Initial seed.",
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


def build_submission_script(args, timestamp, config, benchmark, path):
    seed = args.seed
    root = args.results_dir / args.dataset / benchmark / timestamp / config["name"]
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
    if root.is_absolute():
        result_root = quote(str(root))
    else:
        result_root = '"$REPO_DIR"/' + quote(str(root))
    return SUBMISSION_TEMPLATE.format(
        result_root=result_root,
        pjm_group=args.pjm_group,
        job_name=f"EvoT_{config['name']}_{benchmark}_s{seed}",
        resource_group="small",
        elapse=args.elapse,
        nodes=args.nodes or args.population_size + 1,
        env="\n".join(config["env"]),
        flags="\n".join(f"  {quote(f)}" for f in flags),
        seed=seed,
    )


def main():
    args = get_parser().parse_args()
    bms = args.benchmarks if args.benchmarks else Polybench.get_benchmarks()
    benchmarks = [Path(str(b)).name for b in bms]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_all = []

    for config in CONFIGS:
        for benchmark in benchmarks:
            filename = f"{benchmark}.sh"
            path = args.output_dir / config["name"] / filename
            relative_path = path.relative_to(args.output_dir)
            run_all.append('"$SCRIPT_DIR"/' + quote(str(relative_path)))
            path.parent.mkdir(parents=True, exist_ok=True)
            body = build_submission_script(args, timestamp, config, benchmark, path)
            path.write_text(body)
            os.chmod(path, 0o755)

    run_all_path = args.output_dir / "run_all.sh"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_all_path.write_text(RUN_ALL_TEMPLATE.format(submission="\n".join(run_all)))
    os.chmod(run_all_path, 0o755)

    print("configs:", ", ".join(config["name"] for config in CONFIGS))
    print("benchmarks:", len(benchmarks))
    print("jobs:", len(run_all))
    print("timestamp:", timestamp)
    print("run all:", run_all_path)


if __name__ == "__main__":
    main()
