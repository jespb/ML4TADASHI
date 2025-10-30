

import argparse
from BeamSearch import BeamSearch
from EvoTADASHI import EvoTADASHI
from Heuristic  import Heuristic

 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=str, default="jacobi-1d")
    parser.add_argument("--dataset", type=str, default="LARGE")
    parser.add_argument("--oflag", type=int, default=3)
    parser.add_argument("--seed", type=int, default=47)
    parser.add_argument("--n-trials", type=int, default=2)
    parser.add_argument("--n-threads", type=int, default=1)
    parser.add_argument("--method", type=str, default="EvoTADASHI")
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--max-gen", type=int, default=10)
    parser.add_argument("--use-heuristic", action=argparse.BooleanOptionalAction)
    parser.add_argument("--beam-width", type=int, default=10)
    parser.add_argument("--max-depth", type=int, default=10)
    parser.add_argument("--allow-omp", action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    if args.method == "EvoTADASHI":
    	method = EvoTADASHI()
    elif args.method == "BeamSearch":
    	method = BeamSearch(args)
    elif args.method == "Heuristic":
    	method = Heuristic(args)

    if args.benchmark == "all":
        pb = [
            "jacobi-1d",
            "bicg",
            "atax",
            "gesummv",
            "trisolv",
            "durbin",
            "mvt",
            "gemver",
            "deriche",
            "doitgen",
            "gemm",
            "syrk",
            "2mm",
            "trmm",
            "symm",
            "jacobi-2d",
            "fdtd-2d",
            "cholesky",
            "syr2k",
            "3mm",
            "correlation",
            "covariance",
            "heat-3d",
            "gramschmidt",
            "ludcmp",
            "lu",
            "nussinov",
            "adi",
            "floyd-warshall",
            "seidel-2d",
        ]
        pb = pb[:]
        for benchmark in pb:
            print("\n\n\n")
            args.benchmark = benchmark
            print(str(args) + "\n")
            method.fit()
    else:
        print(str(args) + "\n")
        method.fit()