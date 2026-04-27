
from tadashi.apps import Polybench

pbb = Polybench.get_benchmarks()
pbb = [ str(p) for p in pbb ]
print(pbb)

llvm = [
    "source /home/apps/oss/llvm-v19.1.4/init.sh",
    "module load LLVM/llvmorg-21.1.0",
]
llvmv = ["llvm19", "llvm21"]


to_run = []

population_size = 300
max_gen = 20

for li in range(len(llvm)):
    l = llvm[li]
    lv = llvmv[li]
    for b in pbb:
        bn = b.split("/")[-1]

        print("mpirun -n 1 python -u ML4TADASHI/main_ML4T.py --n-threads 2 --method FugakuEvoTADASHI --population-size %d --max-gen %d --dataset EXTRALARGE --benchmark %s " % (population_size, max_gen, b) )

        pj = [
        "#!/bin/bash ",
        "#PJM -g ra000012 ",
        "#PJM -x PJM_LLIO_GFSCACHE=/vol0004 ",
        "#PJM -N EvoT_%s_%s " % (lv, bn),
        "#PJM -L rscgrp=small ",
        "#PJM -L elapse=21:00:00 ",
        "#PJM -L node=%d " % (population_size + 1),
        "#PJM --mpi \"max-proc-per-node=1\" ",
        "# #PJM --llio localtmp-size=40Gi ",
        "#PJM -j -S ",
        "set -e ",
        "",
        "function set_env (){ ",
        "  export PATH=\"$1/bin${PATH:+:${PATH}}\" ",
        "  export PATH=\"$1/bin64${PATH:+:${PATH}}\" ",
        "  export LD_LIBRARY_PATH=\"$1/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}\" ",
        "  export LIBRARY_PATH=\"$1/lib${LIBRARY_PATH:+:${LIBRARY_PATH}}\" ",
        "  export LD_LIBRARY_PATH=\"$1/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}\" ",
        "  export LIBRARY_PATH=\"$1/lib64${LIBRARY_PATH:+:${LIBRARY_PATH}}\" ",
        "  export C_INCLUDE_PATH=\"$1/include${C_INCLUDE_PATH:+:${C_INCLUDE_PATH}}\" ",
        "  export CPLUS_INCLUDE_PATH=\"$1/include${CPLUS_INCLUDE_PATH:+:${CPLUS_INCLUDE_PATH}}\" ",
        "  export MAN_PATH=\"$1/man${MAN_PATH:+:${MAN_PATH}}\" ",
        "}",
        "",
        "export TMPDIR=/worktmp",
        "export LD_PRELOAD=/usr/lib/FJSVtcs/ple/lib64/libpmix.so", 
        "",
        l,
        "mpirun -n 1 python -u ML4TADASHI/main_ML4T.py --n-threads 2 --method FugakuEvoTADASHI --population-size %d --max-gen %d --dataset EXTRALARGE --benchmark %s " % (population_size, max_gen, b),
        ]

        filename="pjsub_evot_%s_%s.sh"%(lv,bn)
        f = open(filename, "w")
        f.write( "\n".join(pj) )
        f.close()

        to_run.append("pjsub " + filename)

f = open("run_all.sh", "w")
for tr in to_run:
    f.write(tr + "\n")
f.close()

