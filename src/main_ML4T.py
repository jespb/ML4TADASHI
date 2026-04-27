
import argparse

from tadashi.apps import Polybench, Simple

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=str, default="stencils/jacobi-1d")
    parser.add_argument("--base", type=str, default="examples/polybench")
    parser.add_argument("--dataset", type=str, default="LARGE")
    parser.add_argument("--oflag", type=int, default=3)
    parser.add_argument("--seed", type=int, default=47)
    parser.add_argument("--n-trials", type=int, default=2)
    parser.add_argument("--method", type=str, default="EvoTADASHI")
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--tournament-size", type=int, default=2)
    parser.add_argument("--max-gen", type=int, default=10)
    parser.add_argument("--use-heuristic", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--beam-width", type=int, default=10)
    parser.add_argument("--max-depth", type=int, default=10)
    parser.add_argument("--use-mpi", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--cls", type=str, default="")
    args = parser.parse_args()


    translator = None
    if args.cls.lower() == "polly":
        from tadashi.translators import Polly
        translator = Polly()

    app = Polybench(args.benchmark, compiler_options=["-D%s_DATASET" % args.dataset, "-O%d"%args.oflag])

    if args.method == "EvoTADASHI":
        from EvoTADASHI import EvoTADASHI
        method = EvoTADASHI(args, app)
    elif args.method == "BeamSearch":
        from BeamSearch import BeamSearch
        method = BeamSearch(args)
    elif args.method == "Heuristic":
        from Heuristic import Heuristic
        method = Heuristic(args)
    else:
        print("Method not implemented %s" % args.method)
        assert False


    print(str(args) + "\n")
    method.fit()
