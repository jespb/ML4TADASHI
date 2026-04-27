#!/bin/bash
#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -N ML4TADASHI
#PJM -L rscgrp=small
#PJM -L elapse=3:00:00
#PJM -L node=5
#PJM --mpi "max-proc-per-node=1"
# #PJM --llio localtmp-size=40Gi
#PJM -j -S

set -e

export TMPDIR=/worktmp
export LD_PRELOAD=/usr/lib/FJSVtcs/ple/lib64/libpmix.so 

#source /home/apps/oss/llvm-v19.1.4/init.sh		  
#mpirun -n 1 python -u ML4TADASHI/main_ML4T.py --n-threads 2 --method FugakuEvoTADASHI --population-size 20 --max-gen 5 --dataset "EXTRALARGE" --benchmark "linear-algebra/blas/gemm"


module load LLVM/llvmorg-21.1.0
mpirun -n 1 python -u ML4TADASHI/main_ML4T.py --n-threads 2 --method FugakuEvoTADASHI --population-size 20 --max-gen 5 --dataset "EXTRALARGE" --benchmark "linear-algebra/blas/gemm"

#mpirun -n 1 python -u ML4TADASHI/main_ML4T.py --n-threads 2 --method FugakuEvoTADASHI --population-size 300 --max-gen 50 --dataset "EXTRALARGE" --benchmark "datamining/correlation" 
