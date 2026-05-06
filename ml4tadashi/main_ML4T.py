import argparse

from tadashi import translators
from tadashi.apps import Polybench, Simple

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cls", type=str, choices=["Pet", "Polly"], default="Pet")
    parser.add_argument("--benchmark", type=str, default="stencils/jacobi-1d")
    parser.add_argument("--base", type=str, default="examples/polybench")
    parser.add_argument("--dataset", type=str, default="LARGE")
    parser.add_argument("--oflag", type=int, default=3)

    parser.add_argument("--method", type=str, default="EvoTADASHI")

    parser.add_argument("--init_seed", type=int, default=47)
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--tournament-size", type=int, default=2)
    parser.add_argument("--max-gen", type=int, default=10)
    parser.add_argument("--n-trials", type=int, default=2)
    parser.add_argument(
        "--use-mpi", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument(
        "--use-heuristic", action=argparse.BooleanOptionalAction, default=False
    )

    parser.add_argument("--max-depth", type=int, default=10)
    parser.add_argument("--beam-width", type=int, default=10)
    args = parser.parse_args()

    translator = None
    if args.cls == "Polly":
        translator = translators.Polly()
    else:
        translator = translators.Pet()

    app = Polybench(
        args.benchmark,
        compiler_options=[f"-D{args.dataset}_DATASET", f"-O{args.oflag}"],
        translator=translator,
    )

    if args.method == "EvoTADASHI":
        from EvoTADASHI import EvoTADASHI

        method = EvoTADASHI(
            app,
            args.init_seed,
            args.population_size,
            args.tournament_size,
            args.max_gen,
            args.n_trials,
            args.use_mpi,
            args.use_heuristic,
        )
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
