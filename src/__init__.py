import argparse


def get_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=47)
    parser.add_argument("--n-trials", type=int, default=2)
    parser.add_argument("--n-threads", type=int, default=1)
    parser.add_argument("--method", type=str, default="EvoTADASHI")
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--tournament-size", type=int, default=2)
    parser.add_argument("--max-gen", type=int, default=10)
    parser.add_argument("--use-heuristic", action=argparse.BooleanOptionalAction)
    parser.add_argument("--beam-width", type=int, default=10)
    parser.add_argument("--max-depth", type=int, default=10)
    parser.add_argument("--allow-omp", action=argparse.BooleanOptionalAction)
    return parser.parse_args(argv)


def run(cls, kwargs, argv=None):
    args = get_args(argv)
    args.cls = cls
    args.kwargs = kwargs
    if args.method == "EvoTADASHI":
        from EvoTADASHI import EvoTADASHI
    elif args.method == "FugakuEvoTADASHI":
        from EvoTADASHI_fugaku import EvoTADASHI
    elif args.method == "BeamSearch":
        from BeamSearch import BeamSearch
    elif args.method == "Heuristic":
        from Heuristic import Heuristic
    else:
        print("Method not implemented %s" % args.method)
        assert False

    if args.method in ["EvoTADASHI", "FugakuEvoTADASHI"]:
        method = EvoTADASHI(args)
    elif args.method == "BeamSearch":
        method = BeamSearch(args)
    elif args.method == "Heuristic":
        method = Heuristic(args)
    print(str(args) + "\n")
    method.fit()
