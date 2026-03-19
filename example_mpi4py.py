#!/bin/env python

from mpi4py import MPI
from mpi4py.futures import MPIPoolExecutor, as_completed
import socket

import tadashi
from tadashi.apps import Polybench
from tadashi.translators import Polly


def measure_mpi(nco):
    name, co = nco    
    app = Polybench(
            name,
            compiler_options=co,
            translator=Polly(),                                            
    )        
    return app.measure(), socket.gethostname()


            
def main():
    name = "linear-algebra/blas/gemm"
    comp_opt = ["-DEXTRALARGE_DATASET", "-O3"]

    with MPIPoolExecutor(max_workers=3) as executor: 
        futures = [
                executor.submit(measure_mpi, (name, comp_opt))
                for _ in range(3)
        ]
        for f in as_completed(futures):
            print(f"{f=} {f.result(5)=}")


if __name__ == "__main__":
    main()
