#!/bin/bash
#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -N ML4TADASHI
#PJM -L rscgrp=small
#PJM -L elapse=1:00:00
#PJM -L node=2
#PJM --mpi "max-proc-per-node=1"
# #PJM --llio localtmp-size=40Gi
#PJM -j -S
set -e

function set_env (){
  export PATH="$1/bin${PATH:+:${PATH}}"
  export PATH="$1/bin64${PATH:+:${PATH}}"
  export LD_LIBRARY_PATH="$1/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  export LIBRARY_PATH="$1/lib${LIBRARY_PATH:+:${LIBRARY_PATH}}"
  export LD_LIBRARY_PATH="$1/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  export LIBRARY_PATH="$1/lib64${LIBRARY_PATH:+:${LIBRARY_PATH}}"
  export C_INCLUDE_PATH="$1/include${C_INCLUDE_PATH:+:${C_INCLUDE_PATH}}"
  export CPLUS_INCLUDE_PATH="$1/include${CPLUS_INCLUDE_PATH:+:${CPLUS_INCLUDE_PATH}}"
  export MAN_PATH="$1/man${MAN_PATH:+:${MAN_PATH}}"
}

source /home/apps/oss/llvm-v19.1.4/init.sh
		  
mpiexec python ML4TADASHI/example_mpi4py.py
